# 🌌 Cursor Portal: Your Gateway to the Digital Universe

> Because real hackers never leave their IDE

## 🚀 Vision

Transform Cursor into your singular interface to the digital world. No more context switching, no more leaving your comfort zone. Write code, create content, and share your brilliance with the world—all from within your IDE.
 
- Blog about your latest hack without opening a browser
- Generate and edit videos without touching another app
- Share your genius with the world without leaving your safe space

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
- More platform integrations
- Ordering pizza 

## 🛠 How to Use

### Setup

> ⚠️ **Note:** Currently, only Python MCP servers are supported in Cursor. Node.js servers are not yet working with the Cursor MCP protocol.

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
HEYGEN_API_KEY=your_heygen_api_key

# servers/creative/heygen-python-mcp/.env
HEYGEN_API_KEY=your_heygen_api_key
```

Add MCP servers in cursor settings using the command option:
path-to-venv path-to-server.py

### Basic Usage

Open composer in Cursor (cmd+l) and select Claude agent.

#### Writing a Blog Post
1. Start a conversation with Claude and mention you want to use the blog MCP:
```
"Hey, I'd like to write a blog post about [your topic]"
```

2. Claude will help you create the post using these commands:
```python
# Create a new draft
mcp_create_ghost_post(
    title="Your Amazing Title",
    html_content="<p>Your content with HTML formatting</p>",
    status="draft"
)

# Add images
mcp_add_image_to_post(
    post_id="your_post_id",
    image_url="https://your-image-url.com/image.jpg"
)

# Edit the post
mcp_edit_ghost_post(
    post_id="your_post_id",
    title="Updated Title",
    html_content="<p>Updated content</p>"
)

# When ready to publish
mcp_edit_ghost_post(
    post_id="your_post_id",
    status="published"
)
```

#### Creating and Adding Videos
1. Generate a video:
```python
# Generate the video
mcp_generate_video(
    script="Your video script here"
)
# Response will include a video_id

# Download the generated video
mcp_download_video(
    video_id="your_video_id"
)

# Upload to Ghost and add to post
mcp_upload_video_to_ghost(
    video_id="your_video_id"
)

# Add to your blog post
mcp_edit_ghost_post(
    post_id="your_post_id",
    video_id="your_video_id",
    video_position="top"  # or "bottom"
)
```

Example conversation flow:
```
You: "I want to create a blog post about my new coding project with a video intro"

Claude: "I'll help you create that. First, let's generate a video introduction..."
[Claude will guide you through the process using the commands above]
```


## 🌟 Why Cursor Portal?

- **Stay in Flow**: No more context switching between applications
- **Streamlined Workflow**: Everything you need, right where you code
- **Developer-First**: Built by developers, for developers
- **Extensible**: Easy to add new integrations and features

Example of a blog post with a video:
https://www.adithyan.blog/p/79ad812b-8c53-4fca-91f7-a5a8930024c3/


## 🙏 Acknowledgments

- [Cursor](https://cursor.sh/) - The amazing IDE that makes this possible
- [Ghost](https://ghost.org/) - The blogging platform we integrate with
- [HeyGen](https://www.heygen.com/) - For their awesome video generation API
- [Speedinvest](https://speedinvest.com/) - For the cosy hackathon atmosphere

---


