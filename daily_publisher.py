import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Confidence Is the Best Outfit — Wear It Daily",
        "5 Outfit Ideas That Scream Elegance",
        "Beauty Tips Every Woman Should Know",
        "How to Elevate Your Style on Any Budget",
        "The Power of Dressing for Yourself",
        "Luxury Vibes Without the Luxury Price Tag",
        "Every Shade of Beauty Deserves to Shine",
        "Style Secrets the Fashion World Keeps",
        "Effortless Glam: Your Daily Beauty Routine",
        "Why Confidence Changes Everything",
        "Accessorize Like You Mean It",
        "Minimal Wardrobe, Maximum Impact",
        "Self-Expression Through Fashion",
        "The Art of Looking Polished Every Day",
        "Embrace Your Beauty in Every Shade",
    ]

    fallback_descriptions = [
        "Fashion isn't about following rules — it's about expressing who you are. Your outfit is your first message to the world, so make it speak confidence, elegance, and self-love. From timeless classics to bold statements, style is personal. Drop a 👑 if you believe confidence is the best outfit! #fashion #style #elegance #luxury #beauty #lifestyle #selfexpression #outfitideas #confidencestyle #zoraniluma",
        "You don't need a big budget to look expensive. Elegance is in the details — clean lines, good fit, and the way you carry yourself. Mix high and low, keep it intentional, and let your personality lead. Style is a superpower we all have. Save this for your next wardrobe refresh! ✨ #fashiontips #styletips #elegance #luxurystyle #affordablefashion #outfitideas #wardrobeessentials #zoraniluma",
        "Beauty is about feeling good in your own skin. A simple skincare routine, the right glow, and a little self-care go a long way. You are beautiful in every shade, every shape, every version of you. This is your reminder to embrace it. Like if this spoke to you! 💖 #beautytips #skincare #selflove #beautyinallshades #glowup #naturalbeauty #confidence #zoraniluma",
        "The most attractive thing you can wear is confidence. When you feel good, it shows — in how you walk, how you smile, how you show up. Build your style around what makes YOU feel powerful, not what others expect. Comment one thing that makes you feel confident! 👑 #confidence #selflove #fashion #empowerment #styleinspo #beauty #mindset #zoraniluma",
        "Luxury is a feeling, not a price tag. It's quality over quantity, intention over impulse, and knowing your worth. You can live a luxurious life on any budget by choosing pieces and moments that bring you joy. Here's how to bring a little luxury into your everyday. ✨ #luxurylifestyle #elegance #lifstyle #qualityoverquantity #luxuryfashion #selfworth #zoraniluma",
        "Your style is your signature — it tells your story before you say a word. Whether you love minimal, bold, classic, or trend-forward, wear what makes you feel alive. Fashion is self-expression, and there are no mistakes, only choices. Share this with someone whose style you love! 💫 #fashion #selfexpression #personalstyle #styleinspiration #trendy #fashionista #zoraniluma",
        "Outfit ideas for the days when you feel like you have nothing to wear — even though your closet is full. Mixing textures, playing with accessories, and one statement piece can transform any look. Save these ideas for your next 'I have nothing to wear' moment! 📸 #outfitideas #ootd #styleinspo #fashiontips #getreadywithme #wardrobe #zoraniluma",
        "Beauty doesn't have one standard — it has infinite shades and shapes. From every skin tone to every curl pattern, beauty is diverse, and you belong in that picture. Stop comparing, start celebrating. You're the muse. Drop a 🌍 if you embrace beauty in every shade! #beautyinallshades #diversity #inclusivebeauty #selflove #naturalbeauty #confidence #zoraniluma",
        "Your daily routine is an act of self-love. The skincare, the outfit, the little rituals — they're not vanity, they're honoring yourself. When you show up for yourself daily, you radiate from the inside out. Start with one small ritual today. 💛 #selfcare #beautyroutine #selflove #skincare #morningroutine #glowup #wellness #zoraniluma",
        "Elegance never goes out of style. It's poise, it's grace, it's knowing when to speak and when to let your presence do the talking. Cultivate it in how you dress, how you move, and how you treat others. Like if elegance is your energy! 🕊️ #elegance #classicstyle #grace #sophistication #timelessfashion #poise #zoraniluma",
        "Luxury self-expression is about showing the world the most refined version of you. It's intentional choices — the perfume you wear, the fabric you choose, the way you accessorize. You don't have to shout to be noticed. Here's to quiet luxury and bold confidence. 💫 #luxurystyle #quientluxury #selfexpression #fashion #elegance #styletips #zoraniluma",
        "Style is a language — what does your outfit say today? Bold and unapologetic, soft and romantic, clean and modern? Every look is a chance to tell a new story. Wear the version of you that feels most like home. Comment what your style says about you! 👗 #fashionstyle #personalstyle #stylelanguage #ootd #fashioninspo #selfexpression #zoraniluma",
        "Daily inspiration for your beauty and style journey. Remember: trends fade, but confidence is forever. Build a wardrobe and a mindset that outlast every season. You are the constant, and you are enough. Save this for the days you need a little reminder. ✨ #dailyinspiration #confidence #fashion #beauty #lifestyle #motivation #selfworth #zoraniluma",
        "The best accessory you can own is self-assurance. Walk into any room like you belong there — because you do. Dress for the life you want, hold your head high, and let your energy do the talking. Tag a friend who needs this reminder today! 👑 #confidence #empowerment #fashion #selflove #mindset #bodypositivity #zoraniluma",
        "Every shade of beauty is worth celebrating — including yours. Fashion and beauty are for everyone, not just a select few. Whatever your style, whatever your look, you bring something unique to the world. Embrace it fully. Drop a 💖 if you're proud of who you are! #beautyinallshades #selflove #fashionforall #confidence #diversity #inclusion #zoraniluma",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "elegant and luxurious — speak like a high-fashion stylist with effortless grace",
        "empowering and confidence-boosting — make viewers feel beautiful and worthy",
        "warm and encouraging — speak like a close friend giving beauty and style advice",
        "bold and glamorous — celebrate self-expression and standing out",
        "aspirational and polished — inspire viewers to elevate their everyday style",
        "inclusive and uplifting — celebrate beauty in every shade and every body",
        "sophisticated and refined — emphasise timeless elegance and quiet luxury",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Zorani Luma'. "
        f"The page covers fashion, beauty, and lifestyle — inspiring elegance, luxury, and self-expression. "
        f"Its motto is 'Confidence is the best outfit.' It shares outfit ideas, beauty tips, and daily inspiration, "
        f"embracing beauty in every shade. It's aspirational, empowering, and speaks to people who love style and self-love. "
        f"Speak as an elegant, confident fashion and beauty influencer who makes people feel beautiful and powerful. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"- Like if this inspired your style! "
        f"- Comment your fashion goal below! "
        f"- Share this with a friend who loves fashion! "
        f"- Follow Zorani Luma for daily fashion and beauty inspiration! "
        f"Include relevant hashtags in ALL LOWERCASE such as #fashion #beauty #lifestyle #elegance #luxury #style #selfexpression #outfitideas #beautytips #confidence #selflove #dailyinspiration #fashionista #zoraniluma. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "beauty", "lifestyle", "elegance", "luxury", "style", "outfitideas", "beautytips", "confidence", "selflove", "fashionista", "dailyinspiration", "selfexpression", "zoraniluma"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
