import { FastMCP } from 'fastmcp';
import { z } from 'zod';
import fetch from 'node-fetch';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory name of current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from the same directory as server.ts
dotenv.config({ path: path.join(__dirname, '.env') });

const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
const OUTPUT_DIR = path.join(path.dirname(new URL(import.meta.url).pathname), 'output');

if (!HEYGEN_API_KEY) {
  process.stderr.write('HEYGEN_API_KEY environment variable is required\n');
  process.exit(1);
}

// Define the parameters schema first
const videoParameters = z.object({
  script: z.string().describe('The script/text content for the video'),
  title: z.string().optional().describe('Title for the video'),
  caption: z.boolean().optional().default(false).describe('Whether to add captions to the video'),
  callback_id: z.string().optional().describe('A custom ID for callback purposes'),
  dimension: z.object({
    width: z.number().optional().default(720),
    height: z.number().optional().default(1280)
  }).optional().describe('The dimensions of the output video')
});

type ToolContext = {
  log: {
    error: (message: string, ...args: any[]) => void;
    info: (message: string, ...args: any[]) => void;
  };
  reportProgress: (progress: { progress: number, total: number }) => Promise<void>;
};

// Define the tool type
type VideoGenerationTool = {
  name: string;
  description: string;
  parameters: typeof videoParameters;
  execute: (args: z.infer<typeof videoParameters>, context: ToolContext) => Promise<any>;
};

// Create the tool with proper typing
const generateVideoTool: VideoGenerationTool = {
  name: 'generateVideo',
  description: 'Generate a video using the HeyGen API V2',
  parameters: videoParameters,
  execute: async (args, { log }) => {
    try {
      log.info('Generating video with parameters:', args);

      const requestBody = {
        caption: args.caption,
        title: args.title,
        callback_id: args.callback_id,
        video_inputs: [{
          character: {
            type: "avatar",
            avatar_id: "Abigail_expressive_2024112501"
          },
          voice: {
            type: "text",
            voice_id: "26b2064088674c80b1e5fc5ab1a068eb",
            input_text: args.script
          }
        }],
        dimension: args.dimension || { width: 720, height: 1280 }
      };

      log.info('Request body:', JSON.stringify(requestBody, null, 2));

      const response = await fetch('https://api.heygen.com/v2/video/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': HEYGEN_API_KEY,
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      // Log the raw response for debugging
      const responseText = await response.text();
      log.info('Raw API Response:', responseText);

      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        log.error('Failed to parse response as JSON:', responseText.substring(0, 500));
        throw new Error('Invalid response from HeyGen API');
      }

      if (!response.ok) {
        log.error('HeyGen API error', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          data
        });
        throw new Error(`Failed to create video: ${data.message || 'Unknown error'}`);
      }

      log.info('Video generation initiated', data);
      return {
        content: [{
          type: "text",
          text: `Video generated successfully. Video ID: ${data.data?.video_id}`
        }]
      };
    } catch (error) {
      log.error('Error in generateVideo tool', {
        error,
        api_key_length: HEYGEN_API_KEY.length,
        api_key_preview: `${HEYGEN_API_KEY.substring(0, 5)}...${HEYGEN_API_KEY.substring(HEYGEN_API_KEY.length - 5)}`
      });
      throw error;
    }
  },
};

// New tool: retrieveVoiceIdsTool to fetch available voice IDs from HeyGen API
const retrieveVoiceIdsTool = {
  name: "retrieveVoiceIds",
  description: "Retrieve available voice IDs from HeyGen API",
  parameters: z.object({}),
  execute: async (_args: {}, { log }: ToolContext): Promise<string> => {
    try {
      log.info("Fetching available voice IDs...");
      const response = await fetch("https://api.heygen.com/v2/voices", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Api-Key": HEYGEN_API_KEY,
          "Accept": "application/json"
        }
      });
      const responseText = await response.text();
      log.info("Raw API Response from voice ids:", responseText);
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        log.error("Failed to parse voice ids response as JSON:", responseText.substring(0, 500));
        throw new Error("Invalid response from HeyGen API when fetching voice IDs");
      }
      if (!response.ok) {
        log.error("HeyGen API error while fetching voice ids", {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          data
        });
        throw new Error(`Failed to fetch voice IDs: ${data.message || "Unknown error"}`);
      }
      log.info("Successfully fetched voice IDs", data);
      return JSON.stringify({
          success: true,
          voices: data.data,
          message: "Fetched available voice IDs successfully",
          details: {
              response: data
          }
      });
    } catch (error) {
      log.error("Error in retrieveVoiceIds tool", { error });
      throw error;
    }
  }
};

// New tool: retrieveAvatarsTool to fetch available avatars from HeyGen API
const retrieveAvatarsTool = {
  name: "retrieveAvatars",
  description: "Retrieve available avatars from HeyGen API",
  parameters: z.object({}),
  execute: async (_args: {}, { log }: ToolContext): Promise<string> => {
    try {
      log.info("Fetching available avatars...");
      const response = await fetch("https://api.heygen.com/v2/avatars", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Api-Key": HEYGEN_API_KEY,
          "Accept": "application/json"
        }
      });
      const responseText = await response.text();
      log.info("Raw API Response from avatars:", responseText);
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (e) {
        log.error("Failed to parse avatars response as JSON:", responseText.substring(0, 500));
        throw new Error("Invalid response from HeyGen API when fetching avatars");
      }
      if (!response.ok) {
        log.error("HeyGen API error while fetching avatars", {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          data
        });
        throw new Error(`Failed to fetch avatars: ${data.message || "Unknown error"}`);
      }
      log.info("Successfully fetched avatars", data);
      return JSON.stringify({
        success: true,
        avatars: data.data,
        message: "Fetched available avatars successfully",
        details: {
          response: data
        }
      });
    } catch (error) {
      log.error("Error in retrieveAvatars tool", { error });
      throw error;
    }
  }
};

// Updated downloadVideoTool with polling
const downloadVideoTool = {
  name: "downloadVideo",
  description: "Download the generated video from HeyGen API, given its video_id. Polls for video status until completed.",
  parameters: z.object({
    video_id: z.string().describe("ID of the video to download"),
    output_folder: z.string().optional().describe("Local folder to save the video (default: downloaded_videos)"),
    poll_interval: z.number().optional().default(10000).describe("Polling interval in milliseconds"),
    max_retries: z.number().optional().default(30).describe("Maximum number of polling attempts")
  }),
  execute: async (args: { video_id: string, output_folder?: string, poll_interval?: number, max_retries?: number }, { log, reportProgress }: ToolContext): Promise<string> => {
    try {
      const pollInterval = args.poll_interval || 10000;
      const maxRetries = args.max_retries || 30;
      let retries = 0;
      let videoData: any = null;
      let videoStatus = "";
      
      const statusUrl = new URL("https://api.heygen.com/v1/video_status.get");
      statusUrl.searchParams.append("video_id", args.video_id);
      
      // Polling loop for video status
      while (retries < maxRetries) {
        await reportProgress({
          progress: Math.floor((retries / maxRetries) * 90),
          total: 100
        });
        
        const statusResponse = await fetch(statusUrl.toString(), {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "X-Api-Key": HEYGEN_API_KEY,
            "Accept": "application/json"
          }
        });
        
        const statusText = await statusResponse.text();
        let statusData;
        try {
          statusData = JSON.parse(statusText);
        } catch (e) {
          throw new Error("Invalid response from HeyGen API when fetching video status");
        }
        if (!statusResponse.ok) {
          throw new Error(`Failed to fetch video status: ${statusData.message || "Unknown error"}`);
        }
        
        videoStatus = statusData.data.status;
        videoData = statusData.data;
        if (videoStatus === "completed") {
          await reportProgress({
            progress: 90,
            total: 100
          });
          break;
        } else if (videoStatus === "failed") {
          throw new Error(`Video processing failed. Status: ${videoStatus}`);
        } else {
          await new Promise(resolve => setTimeout(resolve, pollInterval));
          retries++;
        }
      }
      
      if (videoStatus !== "completed") {
        return JSON.stringify({
          content: [{
            type: "text",
            text: `Video is not ready for download after ${maxRetries} attempts. Current status: ${videoStatus}.`
          }]
        });
      }
      
      const videoUrl = videoData.video_url;
      if (!videoUrl) {
        throw new Error("Video URL not found in the status response.");
      }
      
      await reportProgress({
        progress: 95,
        total: 100
      });
      
      const videoResponse = await fetch(videoUrl);
      if (!videoResponse.ok) {
        throw new Error(`Failed to download video from URL: ${videoResponse.statusText}`);
      }
      
      const videoBuffer = await videoResponse.arrayBuffer();
      
      const outputFolder = args.output_folder || OUTPUT_DIR;
      if (!fs.existsSync(outputFolder)) {
        fs.mkdirSync(outputFolder, { recursive: true });
      }
      const filePath = path.join(outputFolder, `video_${args.video_id}.mp4`);
      
      fs.writeFileSync(filePath, Buffer.from(videoBuffer));
      await reportProgress({
        progress: 100,
        total: 100
      });
      
      return JSON.stringify({
        content: [{
          type: "text",
          text: `Video downloaded successfully and saved to ${filePath}`
        }]
      });
    } catch (error) {
      throw error;
    }
  }
};

// Create the FastMCP server instance
const server = new FastMCP({
  name: 'Heygen-mcp',
  version: '0.1.0'
});

// Register all tools
server.addTool(generateVideoTool);
server.addTool(retrieveVoiceIdsTool);
server.addTool(retrieveAvatarsTool);
server.addTool(downloadVideoTool);

// Start the server
server.start({
  transportType: "sse",
  sse: {
    endpoint: "/sse",
    port: 8080,
  },
});


