from typing import List, Dict
from openai import OpenAI
from ..config import OPENAI_API_KEY

def translate_segments(segments: List[Dict], target_language: str = "Spanish") -> List[Dict]:
    """
    Translate each segment to target language using OpenAI.
    Preserves timing and speaker information.
    """
    print(f"Translating {len(segments)} segments to {target_language}")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    for i, segment in enumerate(segments):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text to {target_language}. "
                                  f"Maintain the tone and style of the original. Keep the translation concise and natural. "
                                  f"Do not add any explanations, just provide the translation."
                    },
                    {
                        "role": "user",
                        "content": segment['text']
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            segment['text_translated'] = response.choices[0].message.content.strip()
            print(f"Segment {i+1}/{len(segments)}: {segment['text'][:30]}... -> {segment['text_translated'][:30]}...")
            
        except Exception as e:
            print(f"Translation error for segment {i}: {e}")
            segment['text_translated'] = segment['text']
    
    return segments