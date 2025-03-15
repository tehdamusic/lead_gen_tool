import os
import openai
import logging
from typing import Dict, Any, Union, Tuple

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

def score_lead(lead: Dict[str, Any]) -> Tuple[int, str]:
    """
    Score a lead from 1-10 based on their likelihood to purchase a coaching course.
    
    Args:
        lead: Dictionary containing lead information with some of these keys:
              - name: Lead's name
              - job_title: Lead's job title (LinkedIn)
              - description: Lead's description or bio
              - comment: Lead's comment (Instagram)
              - text: Lead's tweet text (Twitter)
              - content: Lead's full content (Twitter)
              - platform: Source platform (LinkedIn, Twitter, Instagram)
    
    Returns:
        Tuple containing:
          - Integer score from 1-10
          - String rationale for the score
    """
    try:
        # Extract relevant information from the lead
        name = lead.get('name', '')
        platform = lead.get('platform', 'unknown')
        
        # Compile all available text data about the lead
        text_data = []
        
        if platform == 'linkedin':
            job_title = lead.get('job_title', '')
            description = lead.get('description', '')
            text_data.extend([f"Name: {name}", f"Job Title: {job_title}", f"Description: {description}"])
        
        elif platform == 'twitter':
            tweet_text = lead.get('text', '')
            content = lead.get('content', '')
            text_data.extend([f"Username: {name}", f"Tweet: {tweet_text}", f"Content: {content}"])
        
        elif platform == 'instagram':
            username = lead.get('username', '')
            comment = lead.get('comment', '')
            text_data.extend([f"Username: {username}", f"Comment: {comment}"])
        
        # Create a prompt for the AI
        prompt = f"""
        Analyze this potential lead for a personal development/career coaching course:
        
        {' '.join(text_data)}
        
        Score this lead from 1-10 based on their likelihood to purchase a coaching course, where:
        1-3: Very low interest - Not a good fit for coaching
        4-6: Moderate interest - Some potential but not ideal
        7-8: High interest - Strong potential for coaching services
        9-10: Very high interest - Ideal candidate for coaching
        
        Focus on these factors:
        - Career frustration or dissatisfaction
        - Desire for change or growth
        - Feeling stuck or overwhelmed
        - Receptiveness to guidance
        - Not being a competitor (coach, mentor, consultant)
        
        Respond with ONLY a JSON object containing:
        {{
            "score": [numeric score 1-10],
            "rationale": [brief explanation for the score]
        }}
        """
        
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a lead scoring assistant that analyzes potential coaching clients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        # Extract and parse the response
        result_text = response.choices[0].message.content.strip()
        
        # Handle possible JSON parsing errors
        try:
            import json
            result = json.loads(result_text)
            score = int(result.get('score', 0))
            rationale = result.get('rationale', 'No rationale provided')
            
            # Ensure score is within bounds
            score = max(1, min(10, score))
            
            return score, rationale
            
        except json.JSONDecodeError:
            logging.error(f"Failed to parse AI response as JSON: {result_text}")
            return 0, "Error: Failed to parse AI response"
        except ValueError:
            logging.error(f"Invalid score value in AI response: {result_text}")
            return 0, "Error: Invalid score value"
            
    except Exception as e:
        logging.error(f"Error in lead scoring: {str(e)}")
        return 0, f"Error: {str(e)}"


def is_qualified_lead(lead: Dict[str, Any], min_score: int = 4) -> bool:
    """
    Determine if a lead qualifies based on their score.
    
    Args:
        lead: Dictionary containing lead information
        min_score: Minimum score required to qualify (default: 4)
        
    Returns:
        Boolean indicating if the lead qualifies
    """
    score, _ = score_lead(lead)
    return score >= min_score
