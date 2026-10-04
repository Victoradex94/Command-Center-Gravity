"""Single-owner, agent-mediated request/response handoff. No Slack client.

Root is the trusted transport executor and provenance/normalization authority.
Raw tool responses are retained; this module never treats Slack text as authority.
"""
from copy import deepcopy
from .model import require
from .slack import Readback, digest
from .slack_controlled import EVENT, WORKSPACE, SENDER

ROOT_ROUTE = 'user_message.send_message(channel=slack)'
ORDER = tuple(EVENT + '/' + label for label in ('activity', 'attention', 'owner'))


class HandoffPending(BaseException):
    """Intentional yield after both adapter attempt and handoff commit."""
    def __init__(self, request):
        self.request = request


class RootHandoff:
    def __init__(self, boundary, allowed):
        self.boundary, self.journal, self.allowed = boundary, boundary.journal, allowed

    def authorize(self, *, approval, identity_evidence, zero_send_evidence,
                  workspace, sender, route):
        require((workspace, sender, route) == (WORKSPACE, SENDER, ROOT_ROUTE),
                'exact approved root bot route required')
        require(all(isinstance(x, str) and x.strip() for x in
                    (approval, identity_evidence, zero_send_evidence)), 'root evidence required')
        authority = dict(approval=approval, identity_evidence=identity_evidence,
                         zero_send_evidence=zero_send_evidence,
                         workspace=workspace, sender=sender, route=route)
        with self.journal.transaction() as state:
            self._binding(state)
            if 'root_handoff' in state:
                require(state['root_handoff']['authority'] == authority, 'authority collision')
                return
            require(not state['controlled_slack']['operations'] and
                    all(state['messages'][k]['attempts'] == 0 and
                        state['messages'][k]['state'] == 'pending' for k in ORDER),
                    'initial zero-send handoff must be pristine')
            state['root_handoff'] = dict(authority=authority, requests={}, evidence=[])

    @staticmethod
    def _binding(state):
        control = state['controlled_slack']
        require(control['fingerprint'] == digest(control['binding']) and
                set(control['binding']) == set(ORDER), 'binding corrupt')
        for key in ORDER:
            require(all(state['messages'][key][f] == value
                        for f, value in control['binding'][key].items()), 'intent changed')
        return control['binding']

    def _gate(self):
        require(self.allowed() is True, 'root permission withdrawn or cancelled')
        state = self.journal.snapshot()
        self._binding(state)
        auth = state['root_handoff']['authority']
        require((auth['workspace'], auth['sender'], auth['route']) ==
                (WORKSPACE, SENDER, ROOT_ROUTE), 'root authority mismatch')

    def prepare_next(self):
        """Return a NEW request once; an unresolved request is never reissued.

        Use status() to reconcile a previously returned request, never resend it.
        """
        self._gate()
        state = self.journal.snapshot()
        for key in ORDER:
            if state['messages'][key]['state'] == 'verified':
                require(state['root_handoff']['requests'].get(key, {}).get('state') == 'verified',
                        'verification must have root receipt evidence')
                continue
            require(key not in state['root_handoff']['requests'] and
                    state['messages'][key]['attempts'] == 0 and
                    state['messages'][key]['state'] == 'pending',
                    'unresolved attempt: reconcile, never reissue')
            try:
                self.boundary.deliver(key, self)
            except HandoffPending as handoff:
                return handoff.request
            raise ValueError('handoff not reserved; inspect journal, no unchanged retry')
        return None

    def inspect(self, key, destination, thread):
        self._gate()
        state = self.journal.snapshot()
        item = self._binding(state)[key]
        require((destination, thread) == (item['destination'], item['thread']), 'target mismatch')
        req = state['root_handoff']['requests'].get(key)
        if req and req['state'] == 'verified':
            return Readback('found', key, destination, thread, item['text'], req['reference'])
        # Root's explicit initial zero-send attestation is scoped to these exclusive
        # immutable operations. This is not an inference from incomplete Slack history.
        if not req and state['messages'][key]['attempts'] == 0:
            return Readback('absent')
        return Readback('unknown')

    def send(self, key, destination, thread, text):
        self._gate()
        with self.journal.transaction() as state:
            binding = self._binding(state)
            item = binding[key]
            handoff = state['root_handoff']
            require(all(state['messages'][k]['state'] == 'verified' and
                        handoff['requests'].get(k, {}).get('state') == 'verified'
                        for k in ORDER[:ORDER.index(key)]), 'prior operation not verified')
            require(key not in handoff['requests'] and
                    key not in state['controlled_slack']['operations'], 'reserved operation cannot replay')
            require((destination, thread, text) ==
                    (item['destination'], item['thread'], item['text']), 'payload mismatch')
            m = state['messages'][key]
            require(m['state'] == 'sending' and m['attempts'] == 1, 'adapter reservation required')
            request = dict(operation_id=key, attempt_id=key + '/send-attempt-1',
                           route=ROOT_ROUTE, workspace=WORKSPACE, sender=SENDER,
                           destination=destination, thread=thread, content=text,
                           binding_sha256=state['controlled_slack']['fingerprint'])
            request['request_sha256'] = digest(request)
            handoff['requests'][key] = dict(request=request, state='reserved', reference='')
            state['controlled_slack']['operations'][key] = dict(
                state='root-request-reserved', calls=1, request_sha256=request['request_sha256'])
        raise HandoffPending(deepcopy(request))

    def reconcile(self, request_sha256, *, raw_response=None, acceptance=None,
                  raw_readback=None, observation=None):
        """Trusted root supplies originals and normalized fields, not generated receipts.

        acceptance: workspace/sender/destination/reference; observation adds
        thread/text. Both reference the actual Slack message ID. Mismatches freeze.
        Positive exact readback may settle a lost send response; absence never retries.
        Reconciliation is allowed after withdrawal because it causes no send.
        """
        with self.journal.transaction() as state:
            self._binding(state)
            handoff = state['root_handoff']
            matches = [(key, value) for key, value in handoff['requests'].items()
                       if value['request']['request_sha256'] == request_sha256]
            require(len(matches) == 1, 'unknown request receipt')
            key, record = matches[0]
            req = record['request']
            require(digest({k:v for k,v in req.items() if k != 'request_sha256'}) == request_sha256,
                    'request corrupt')
            evidence = dict(request_sha256=request_sha256, raw_response=raw_response,
                            acceptance=acceptance, raw_readback=raw_readback, observation=observation)
            if evidence not in handoff['evidence']:
                handoff['evidence'].append(deepcopy(evidence))
            def exact(value):
                return (isinstance(value, dict) and bool(value.get('reference')) and
                        all(value.get(f) == req[f] for f in ('workspace', 'sender', 'destination')))
            accepted = bool(raw_response) and exact(acceptance)
            previous = record['reference']
            if accepted and previous and acceptance['reference'] != previous:
                accepted = False
            verified = (bool(raw_readback) and exact(observation) and
                        observation.get('thread') == req['thread'] and
                        observation.get('text') == req['content'] and
                        (not previous or observation['reference'] == previous) and
                        (not accepted or observation['reference'] == acceptance['reference']))
            # Supplying contradictory acceptance cannot be ignored in favor of readback.
            if acceptance is not None and not accepted:
                verified = False
            if record['state'] == 'verified':
                return 'verified'  # retain original proof, never replay later deletion
            outcome = 'verified' if verified else 'accepted' if accepted else 'unknown'
            reference = (observation['reference'] if verified else
                         acceptance['reference'] if accepted else previous)
            record.update(state=outcome, reference=reference)
            state['messages'][key].update(state=outcome, reference=reference)
            state['controlled_slack']['operations'][key].update(state=outcome, reference=reference)
            return outcome

    def status(self):
        return deepcopy(self.journal.snapshot()['root_handoff'])
