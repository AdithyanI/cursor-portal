# 🌌 Cursor Portal: Your Gateway to the Digital Universe

> Because real hackers never leave their IDE

## 🚀 Vision

Transform Cursor into your singular interface to the digital world. No more context switching, no more leaving your safe space. Write code, create content, and share your brilliance with the world—all from within your IDE.

## 🎯 Mission

Cursor Portal is built for hackers who believe their IDE should be more than just a code editor. It's for those who want to:
- Blog about their latest hack without opening a browser
- Generate and edit videos without touching another app
- Easily order a pizza without leaving Cursor

## ✨ Current Features

### 📝 Blog Integration
- Create and publish blog posts directly from Cursor
- Embed media (images, videos) seamlessly
- Manage your Ghost blog without touching the admin panel

### 🎬 Video Creation
- Generate AI videos using HeyGen
- Edit and customize videos
- Upload and embed videos in your blog posts

### 🔮 Coming Soon
- Social media integration
- Direct image generation and editing
- Ordering food from your favorite restaurants
- More platform integrations

## 🛠 How to Use

### Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/cursor-portal.git
cd cursor-portal
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
```bash
# Create .env files in respective directories:
# servers/blog/.env
GHOST_ADMIN_API_URL=your_ghost_url
GHOST_ADMIN_API_KEY=your_api_key

# servers/creative/heygen-python-mcp/.env
HEYGEN_API_KEY=your_heygen_api_key
```

### Connecting to Cursor

1. In Cursor, open Command Palette (Cmd/Ctrl + Shift + P)
2. Select "MCP: Add Server"
3. Enter the following details:
   - Python Path: `path-to-your-venv/bin/python`
   - Server Path: `path-to-cursor-portal/servers/blog/ghost_mcp_server.py`
   - Transport: `stdio`

For example:
```bash
# Blog Server
Python Path: /Users/you/cursor-portal/venv/bin/python
Server Path: /Users/you/cursor-portal/servers/blog/ghost_mcp_server.py

# Video Generation Server
Python Path: /Users/you/cursor-portal/venv/bin/python
Server Path: /Users/you/cursor-portal/servers/creative/heygen-python-mcp/heygen-mcp-server.py
```

### Using the Portal

1. Open Cursor's chat (Cmd/Ctrl + L)
2. Enter Composer Mode (this activates Claude agent)
3. Reference the MCP servers by their capabilities:

#### Blog Posts
```python
# Create a new blog post
"Hey Claude, create a blog post about my latest project"

# List recent posts
"Show me my recent blog posts"

# Edit an existing post
"Update my last blog post with a new section about..."
```

#### Video Generation
```python
# Generate a new video
"Generate a video saying 'Hello World!'"

# Download and embed a video in a blog post
"Add the last generated video to my blog post"
```

### Available Commands

#### Blog Server
- `mcp_create_ghost_post` - Create a new blog post
- `mcp_list_recent_posts` - List recent posts
- `mcp_edit_ghost_post` - Edit an existing post
- `mcp_delete_ghost_post` - Delete a post
- `mcp_upload_video_to_ghost` - Upload a video to Ghost
- `mcp_add_image_to_post` - Add an image to a post

#### Video Server
- `mcp_generate_video` - Generate a new video
- `mcp_download_video` - Download a generated video
- `mcp_retrieve_voices` - List available voices
- `mcp_retrieve_avatars` - List available avatars

## 🌟 Why Cursor Portal?

- **Stay in Flow**: No more context switching between applications
- **Streamlined Workflow**: Everything you need, right where you code
- **Developer-First**: Built by developers, for developers
- **Extensible**: Easy to add new integrations and features

example of blog with video:
https://www.adithyan.blog/p/79ad812b-8c53-4fca-91f7-a5a8930024c3/
## 🤝 Contributing

We welcome contributions! Whether it's adding new features, improving documentation, or reporting bugs, every contribution helps make Cursor Portal better.



## 🙏 Acknowledgments

- [Cursor](https://cursor.sh/) - The amazing IDE that makes this possible
- [Ghost](https://ghost.org/) - The blogging platform we integrate with
- [HeyGen](https://www.heygen.com/) - For their awesome video generation API
- [speedinvest](https://speedinvest.com/) - For the cosy hackathon atmosphere

---


