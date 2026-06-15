import argparse
from datetime import datetime
from pathlib import Path
import json
import logging
import shutil
import sys
import os
import base64
import requests
from dotenv import load_dotenv

from .config import Config, get_client, get_model
from .frame import VideoProcessor
from .prompt import PromptLoader
from .analyzer import VideoAnalyzer
from .audio_processor import AudioProcessor
from .clients.ollama import OllamaClient
from .clients.generic_openai_api import GenericOpenAIAPIClient
from .link_processor import LinkProcessor

load_dotenv()

# Initialize logger at module level
logger = logging.getLogger(__name__)
logging.getLogger(__name__).setLevel(logging.WARNING)

def get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant."""
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)

def cleanup_files(output_dir: Path):
    """Clean up temporary files and directories."""
    try:
        frames_dir = output_dir / "frames"
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
            logger.debug(f"Cleaned up frames directory: {frames_dir}")
            
        audio_file = output_dir / "audio.wav"
        if audio_file.exists():
            audio_file.unlink()
            logger.debug(f"Cleaned up audio file: {audio_file}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def create_client(config: Config):
    """Create the appropriate client based on configuration."""
    client_type = config.get("clients", {}).get("default", "ollama")
    client_config = get_client(config)
    
    if client_type == "ollama":
        return OllamaClient(client_config["url"])
    elif client_type == "openai_api":
        return GenericOpenAIAPIClient(client_config["api_key"], client_config["api_url"])
    else:
        raise ValueError(f"Unknown client type: {client_type}")

def main():
    parser = argparse.ArgumentParser(description="Analyze video using Vision models")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    parser.add_argument("--video-link", type=str, help="Link of video", default="")
    parser.add_argument("--config", type=str, default="config",
                        help="Path to configuration directory")
    parser.add_argument("--output", type=str, help="Output directory for analysis results")
    parser.add_argument("--client", type=str, help="Client to use (ollama or openrouter)")
    parser.add_argument("--ollama-url", type=str, help="URL for the Ollama service")
    parser.add_argument("--api-key", type=str, help="API key for OpenAI-compatible service")
    parser.add_argument("--api-url", type=str, help="API URL for OpenAI-compatible API")
    parser.add_argument("--model", type=str, help="Name of the vision model to use")
    parser.add_argument("--duration", type=float, help="Duration in seconds to process")
    parser.add_argument("--keep-frames", action="store_true", help="Keep extracted frames after analysis")
    parser.add_argument("--whisper-model", type=str, help="Whisper model size (tiny, base, small, medium, large), or path to local Whisper model snapshot")
    parser.add_argument("--start-stage", type=int, default=1, help="Stage to start processing from (1-3)")
    parser.add_argument("--max-frames", type=int, default=sys.maxsize, help="Maximum number of frames to process")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level (default: INFO)")
    parser.add_argument("--prompt", type=str, default="",
                        help="Question to ask about the video")
    parser.add_argument("--language", type=str, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--temperature", type=float, help="Temperature for LLM generation")
    args = parser.parse_args()

    # Set up logging with specified level
    log_level = get_log_level(args.log_level)
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True  # Force reconfiguration of the root logger
    )
    # Ensure our module logger has the correct level
    logger.setLevel(log_level)

    # Load and update configuration
    config = Config(args.config)
    config.update_from_args(args)

    # Initialize components
    video_path = Path(args.video_path)
    output_dir = Path(config.get("output_dir"))
    client = create_client(config)
    model = get_model(config)
    prompt_loader = PromptLoader(config.get("prompt_dir"), config.get("prompts", []))
    
    try:
        transcript = None
        frames = []
        frame_analyses = []
        video_description = None
        
        # Stage 1: Frame and Audio Processing
        if args.start_stage <= 1:
            # Initialize audio processor and extract transcript, the AudioProcessor accept following parameters that can be set in config.json:
            # language (str): Language code for audio transcription (default: None)
            # whisper_model (str): Whisper model size or path (default: "medium")
            # device (str): Device to use for audio processing (default: "cpu")
            logger.debug("Initializing audio processing...")
            audio_processor = AudioProcessor(language=config.get("audio", {}).get("language", ""), 
                                             model_size_or_path=config.get("audio", {}).get("whisper_model", "medium"),
                                             device=config.get("audio", {}).get("device", "cpu"))
            
            logger.info("Extracting audio from video...")
            try:
                audio_path = audio_processor.extract_audio(video_path, output_dir)
            except Exception as e:
                logger.error(f"Error extracting audio: {e}")
                audio_path = None
            
            if audio_path is None:
                logger.debug("No audio found in video - skipping transcription")
                transcript = None
            else:
                logger.info("Transcribing audio...")
                transcript = audio_processor.transcribe(audio_path)
                if transcript is None:
                    logger.warning("Could not generate reliable transcript. Proceeding with video analysis only.")
            
            logger.info(f"Extracting frames from video using model {model}...")
            processor = VideoProcessor(
                video_path, 
                output_dir / "frames", 
                model
            )
            frames = processor.extract_keyframes(
                frames_per_minute=config.get("frames", {}).get("per_minute", 60),
                duration=config.get("duration"),
                max_frames=args.max_frames
            )
            
        # # Stage 2.5: Extract Video Information and Author
        link_processor = LinkProcessor()
        data_instagram,shortcode = link_processor.scrape_instagram_reel(args.video_link)
        print(data_instagram)
        
        # # Stage 2: Frame Analysis
        # if args.start_stage <= 2:
        #     logger.info("Analyzing frames...")
        #     analyzer = VideoAnalyzer(
        #         client, 
        #         model, 
        #         prompt_loader,
        #         config.get("clients", {}).get("temperature", 0.2),
        #         config.get("prompt", "")
        #     )
        #     frame_analyses = []
        #     for frame in frames:
        #         analysis = analyzer.analyze_frame(frame)
        #         frame_analyses.append(analysis)
                
        # # Stage 3: Video Reconstruction
        # # if args.start_stage <= 3:
        #     logger.info("Reconstructing video description...")
        #     video_description = analyzer.reconstruct_video(
        #         frame_analyses, frames, transcript
        #     )

        API_KEY = config.get("clients", {}).get("openai_api", {}).get("api_key",""), 
        MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"

        # Carpeta donde están tus frames
        IMAGE_FOLDER = output_dir / "frames"  # cambia esto

        # =========================
        # FUNCIONES
        # =========================
        def encode_image(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        def load_images_from_folder(folder, max_images=10):
            images = []
            
            files = sorted(os.listdir(folder))[:max_images]
            
            for file in files:
                path = os.path.join(folder, file)
                if os.path.isfile(path) and file.lower().endswith((".jpg", ".jpeg", ".png")):
                    base64_img = encode_image(path)
                    images.append(base64_img)
            
            return images

        # =========================
        # PREPARAR CONTENIDO
        # =========================
        images_base64 = load_images_from_folder(IMAGE_FOLDER)
        transcript_prompt = " "  if transcript is None else transcript.text
        frames_prompt = ""
        for frame in frames:
            frame_number = frame.number
            frame_timestamp = frame.timestamp
            frame_score = frame.score
            frames_prompt += f"Frame #{frame_number} | Timestamp: {frame_timestamp} | Score: {frame_score}\n" 
            
        with open("prompts/frame_analysis/describe.txt", "r") as f:
            contenido = f.read()
        
        
        commentaries = "".join( x.text + "\n" for x in data_instagram.preview_comments)

        prompt = contenido.format(FRAME_NOTES=frames_prompt,
                                  TRANSCRIPT=transcript_prompt,
                                  DURATION=processor.duration,
                                  LINK=args.video_link,
                                  DATE=datetime.fromtimestamp(data_instagram.caption.created_at).strftime("%Y-%m-%d"),
                                  LIKES=data_instagram.like_count,
                                  AUTHOR=data_instagram.owner.username,
                                  CAPTION=data_instagram.caption.text,
                                  COMMENTARIES=commentaries
                                  )

        
        
        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        # Agregar imágenes al contenido
        for img in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img}"
                }
            })

        # =========================
        # REQUEST
        # =========================
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "reasoning": {"enabled": True}
            })
        )

        # =========================
        # OUTPUT
        # =========================
        result = response.json()

        if "choices" in result:
            logger.info(json.dumps(result))
        else:
            raise ValueError(f"Error: Error en el resultado de la IA: {json.dumps(result, indent=2)}")
            

        
        
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {
            "metadata": {
                "client": config.get("clients", {}).get("default"),
                "model": model,
                "whisper_model": config.get("audio", {}).get("whisper_model"),
                "frames_per_minute": config.get("frames", {}).get("per_minute"),
                "duration_processed": config.get("duration"),
                "frames_extracted": len(frames),
                "frames_processed": min(len(frames), args.max_frames),
                "start_stage": args.start_stage,
                "audio_language": transcript.language if transcript else None,
                "transcription_successful": transcript is not None
            },
            "transcript": {
                "text": transcript.text if transcript else None,
                "segments": transcript.segments if transcript else None
            } if transcript else None,
            "video_description": result["choices"][0]["message"]["content"],
            "video_link": args.video_link,
            "video_url": data_instagram.video_versions[0].url,
            "video_author": data_instagram.owner.username,
            "profile_pic_url":data_instagram.owner.profile_pic_url,
            "caption":data_instagram.caption.text,
            "transcript":transcript_prompt,
            "thumbnail":data_instagram.display_uri,
        }
        
        print(json.dumps(results))
        
        with open(output_dir / f"{shortcode}.json", "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info("\nTranscript:")
        if transcript:
            logger.info(transcript.text)
        else:
            logger.info("No reliable transcript available")
            
        if video_description:
            logger.info("\nVideo Description:")
            logger.info(video_description.get("response", "No description generated"))
        
        if not config.get("keep_frames"):
            cleanup_files(output_dir)
        
        logger.info(f"Analysis complete. Results saved to {output_dir / 'analysis.json'}")
            
    except Exception as e:
        logger.error(f"Error during video analysis: {e}")
        if not config.get("keep_frames"):
            cleanup_files(output_dir)
        print(f"Error: {e}", file=sys.stderr)
        raise
        

if __name__ == "__main__":
    main()
