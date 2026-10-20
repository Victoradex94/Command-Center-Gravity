from pathlib import Path
import base64,json,re,zipfile
root=Path(__file__).resolve().parents[1]
html=(root/'dist/index.html').read_text()
if 'href="vicadex-theme.css"' not in html:
    html=html.replace('</head>','<link rel="stylesheet" href="vicadex-theme.css"></head>')
names=['index.html','style.css','vicadex-theme.css','nigeria-states.json']+re.findall(r'<script src="([^"]+)"',html)
assets={'index.html':base64.b64encode(html.encode()).decode()}
dist_dir=str(root/'dist')+'/'
for n in names:
    if n!='index.html':
        with open(dist_dir+n,'rb') as f:
            assets[n]=base64.b64encode(f.read()).decode()
assets['vicadex-theme.css']=base64.b64encode((root/'wordpress/poetics-preview/vicadex-theme.css').read_bytes()).decode()
php="""<?php
/**
 * Plugin Name: Poetics Private Preview
 * Description: Editor-only preview of the Poetics Atlas and fictional Games. No pages are published.
 * Version: 0.1.0
 * Requires PHP: 7.4
 * Author: Vic’Adex
 */
if (!defined('ABSPATH')) { exit; }

function vicadex_poetics_preview_url($asset = 'index.html') {
    return add_query_arg(array('action' => 'vicadex_poetics_preview', 'asset' => $asset), admin_url('admin-post.php'));
}
function vicadex_poetics_preview_frame() {
    if (!current_user_can('edit_pages')) {
        return '<p>Poetics preview is available to signed-in editors only.</p>';
    }
    return '<iframe title="Poetics private preview" src="' . esc_url(vicadex_poetics_preview_url()) . '" style="display:block;width:100%;height:85vh;min-height:600px;border:0;background:#141714" referrerpolicy="same-origin"></iframe>';
}
add_shortcode('poetics_preview', 'vicadex_poetics_preview_frame');
add_action('admin_menu', function () {
    add_menu_page('Poetics Preview', 'Poetics Preview', 'edit_pages', 'vicadex-poetics-preview', function () {
        echo '<div class="wrap"><h1>Poetics — private preview</h1><p>Atlas records and fictional game data remain separate. Entry contributions are local browser drafts, not editorial submissions. Nothing is published automatically.</p>';
        echo vicadex_poetics_preview_frame();
        echo '</div>';
    }, 'dashicons-location-alt', 80);
});
function vicadex_poetics_serve_preview() {
    if (!is_user_logged_in() || !current_user_can('edit_pages')) {
        status_header(403);
        nocache_headers();
        header('X-Robots-Tag: noindex, nofollow, noarchive');
        exit('Poetics preview requires a signed-in editor.');
    }
    $asset = isset($_GET['asset']) && is_string($_GET['asset']) ? wp_unslash($_GET['asset']) : 'index.html';
    $assets = json_decode(base64_decode('ASSET_BUNDLE'), true);
    if (!isset($assets[$asset])) {
        status_header(404);
        exit('Unknown Poetics asset.');
    }
    $content = base64_decode($assets[$asset], true);
    nocache_headers();
    header('Cache-Control: private, no-store, max-age=0');
    header('X-Robots-Tag: noindex, nofollow, noarchive');
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: SAMEORIGIN');
    if ($asset === 'index.html') {
        header('Content-Type: text/html; charset=UTF-8');
        $content = preg_replace_callback('/(src|href)="([^"]+\\.(?:js|css|json))"/', function ($match) use ($assets) {
            return isset($assets[$match[2]]) ? $match[1] . '="' . esc_url(vicadex_poetics_preview_url($match[2])) . '"' : $match[0];
        }, $content);
    } elseif (substr($asset, -3) === '.js') {
        header('Content-Type: application/javascript; charset=UTF-8');
    } elseif (substr($asset, -5) === '.json') {
        header('Content-Type: application/json; charset=UTF-8');
    } else {
        header('Content-Type: text/css; charset=UTF-8');
    }
    echo $content;
    exit;
}
add_action('admin_post_vicadex_poetics_preview', 'vicadex_poetics_serve_preview');
add_action('admin_post_nopriv_vicadex_poetics_preview', 'vicadex_poetics_serve_preview');
"""
php=php.replace('ASSET_BUNDLE',base64.b64encode(json.dumps(assets).encode()).decode())
folder=root/'wordpress/poetics-preview'
folder.mkdir(parents=True,exist_ok=True)
(folder/'poetics-preview.php').write_text(php)
(folder/'readme.txt').write_text("""Poetics Private Preview 0.1.0

Install via Plugins > Add New > Upload Plugin, then activate.
Open the Poetics Preview admin menu while signed in as an editor or administrator.
Optional: insert [poetics_preview] into a draft page or Elementor Shortcode widget.
The preview endpoint and all bundled assets require edit_pages capability.
This plugin creates no pages, changes no theme settings, and adds no database tables.
It does not publish publicly or implement server-side submissions.
Deactivate to remove the admin menu and preview handler. Existing local game progress remains in browser storage.
Includes the current prototype assets; state geometry attribution remains visible in the Atlas.
This is an initial preview adapter, not the completed editorial CMS migration.
PHP lint and live WordPress testing remain required before activation.
""")
out=Path('/workspace/scratch/7425d3f2f479/poetics-private-preview.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for f in folder.iterdir():
        if f.suffix != '.css': z.write(f,'poetics-preview/'+f.name)
assert all(base64.b64decode(assets[n])==(root/'dist'/n).read_bytes() for n in names if n!='index.html')
assert base64.b64decode(assets['index.html']).decode()==html
assert 'ASSET_BUNDLE' not in php
assert "current_user_can('edit_pages')" in php
assert not re.search(r'(register_activation_hook|wp_insert_post|update_option|flush_rewrite_rules)\s*\(',php)
print(f'Built {out}; {len(assets)} assets byte-verified; editor gate and no automatic site changes checked.')
