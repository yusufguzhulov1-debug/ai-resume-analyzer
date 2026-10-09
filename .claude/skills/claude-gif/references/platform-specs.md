# Platform GIF Specifications

Definitive reference for GIF size limits, dimension requirements, and behavior
across all major platforms. Updated April 2026.

## Platform Specifications Table

| Platform | Max File Size | Max Dimensions | Auto-Play | Loops | Format Notes |
|----------|--------------|----------------|-----------|-------|-------------|
| **Discord** (inline) | **256 KB** | 400x400 recommended | Yes (if <256KB) | Infinite | >256KB shows as attachment, requires click |
| **Discord** (Nitro) | 50 MB | No strict limit | Yes (if <10MB) | Infinite | Nitro users get higher upload limit |
| **Discord** (emoji) | 256 KB | 128x128 (resized) | Yes | Infinite | Animated emoji; uploaded at any size, displayed 128x128 |
| **Slack** | **500 KB** | No strict limit | Yes (if <500KB) | Infinite | >500KB shows as file attachment |
| **Twitter/X** | **15 MB** | 1280x1080 max | Yes | Infinite | Converted to MP4 on upload; quality may change |
| **Reddit** | 20 MB | No strict limit | Yes | Infinite | Displayed inline in posts and comments |
| **GitHub** (README) | **10 MB** | No strict limit | Yes | Infinite | Displayed inline in markdown; affects page load |
| **GitHub** (Issues) | 10 MB | No strict limit | Yes | Infinite | Same as README |
| **GitHub** (PR comments) | 10 MB | No strict limit | Yes | Infinite | Same as README |
| **iMessage** | 100 MB | No strict limit | Yes | Infinite | Large GIFs may be slow to send/receive |
| **Email** (general) | **1 MB** | 600px wide max | Varies | Varies | Outlook: first frame only; Gmail: auto-plays |
| **Web** (general) | **2 MB** target | 480-640px wide | Yes | Infinite | Performance best practice; larger kills page speed |
| **Tumblr** | 10 MB | 540px wide (resized) | Yes | Infinite | Dashboard resizes to 540px wide |
| **Facebook** | 8 MB | No strict limit | Auto (converted) | Infinite | Converted to video on upload |
| **Instagram** | N/A | N/A | N/A | N/A | No GIF support; use Giphy stickers in stories |
| **LinkedIn** | 5 MB | No strict limit | Yes | Infinite | Supported in posts and articles |
| **Giphy** | 100 MB (upload) | No strict limit | Yes | Infinite | Optimized on their servers after upload |
| **Tenor** | 100 MB (upload) | No strict limit | Yes | Infinite | Optimized on their servers after upload |
| **WhatsApp** | 16 MB | No strict limit | Yes | Infinite | Sent as "sticker" if <500KB and square |
| **Telegram** | 50 MB | No strict limit | Yes | Infinite | Can also be sent as animated sticker (TGS) |
| **Pinterest** | 20 MB | Minimum 100x200 | Yes | Infinite | Animated pins supported |
| **Notion** | 5 MB (embed) | No strict limit | Yes | Infinite | Larger files may slow page |

## Recommended Settings per Platform

### Discord (256 KB target)
```bash
bash gif_convert.sh --input VIDEO --preset discord --output output.gif
# Settings: 320px, 10fps, 128 colors, bayer:3, stats_mode=diff
```
Tips:
- Keep duration under 3 seconds
- Use simple content with few colors
- Static backgrounds help enormously
- If still over 256KB: reduce to 240px width, 8fps

### Slack (500 KB target)
```bash
bash gif_convert.sh --input VIDEO --preset slack --output output.gif
# Settings: 400px, 12fps, 192 colors, floyd_steinberg
```
Tips:
- 3-5 seconds is comfortable
- More color headroom than Discord
- Floyd-Steinberg dithering is fine at this budget

### Twitter/X (15 MB target)
```bash
bash gif_convert.sh --input VIDEO --preset twitter --output output.gif
# Settings: 480px, 15fps, 256 colors, floyd_steinberg
```
Tips:
- Twitter converts GIFs to MP4 on upload -- quality changes
- Test by uploading; Twitter's converter is unpredictable
- Keep under 5 MB for faster loading in timelines
- Maximum 1280x1080 is enforced; larger gets resized

### Web General (2 MB target)
```bash
bash gif_convert.sh --input VIDEO --preset web --output output.gif
# Settings: 480px, 15fps, 256 colors, floyd_steinberg
```
Tips:
- Consider WebP or AVIF animation instead (better compression)
- Lazy-load GIFs below the fold
- Provide poster image (first frame) for progressive display

### High Quality (10 MB budget)
```bash
bash gif_convert.sh --input VIDEO --preset hq --output output.gif
# Settings: 640px, 20fps, 256 colors, sierra2, stats_mode=diff
```
Tips:
- For situations where quality matters and size is secondary
- Good for presentations, documentation, demos
- 640px is the maximum recommended width for GIFs

### Email (1 MB target)
```bash
bash gif_convert.sh --input VIDEO --width 600 --fps 8 --colors 64 --dither "bayer:bayer_scale=3" --output output.gif
```
Tips:
- **Outlook (desktop)**: Shows only first frame. Design the first frame to be meaningful.
- **Gmail**: Auto-plays. Works well.
- **Apple Mail**: Auto-plays. Works well.
- Keep width at 600px max (email rendering constraint)
- Low FPS (6-8) is fine for email -- recipients aren't expecting smooth animation
- Test in multiple email clients before sending

### GitHub README (10 MB target, 2 MB recommended)
```bash
bash gif_convert.sh --input VIDEO --preset web --output output.gif
```
Tips:
- Even though 10MB is allowed, keep under 2MB for page load performance
- Repository visitors may be on slow connections
- Consider using a thumbnail image that links to the full GIF
- For demo GIFs, 480px wide at 12-15fps is ideal

## Platform Behavior Notes

### Auto-Play Behavior
- **Always auto-plays**: Discord, Slack, Twitter, Reddit, GitHub, Tumblr
- **Auto-plays with settings**: Facebook (users can disable), LinkedIn
- **Never auto-plays**: Outlook desktop (shows first frame)
- **Depends on connection**: Some mobile apps pause auto-play on cellular data

### Conversion on Upload
- **Twitter/X**: Converts GIFs to MP4 on upload. Original GIF is not preserved.
- **Facebook**: Converts to video format. Significant quality change possible.
- **All others**: Store and serve the original GIF file.

### Dimension Resizing
- **Tumblr**: Resizes to 540px wide on dashboard
- **Discord emoji**: Resizes to 128x128
- **Twitter**: Resizes if >1280x1080

## Quick Decision Matrix

| Need | Platform | Target Size | Recommended Preset |
|------|----------|-------------|-------------------|
| Reaction GIF in chat | Discord | 256 KB | discord |
| Team notification | Slack | 500 KB | slack |
| Social media post | Twitter/X | 15 MB (aim for 5 MB) | twitter |
| Documentation demo | GitHub | 2 MB | web |
| Blog post illustration | Website | 2 MB | web |
| Email campaign | Email | 1 MB | custom (600px, 8fps, 64 colors) |
| High-quality showcase | Portfolio | 10 MB | hq |
| Quick share anywhere | General | 2 MB | web |
