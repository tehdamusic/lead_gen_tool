#!/usr/bin/env python3
"""
Script to fix the MessageGenerator compatibility with the web-based Reddit scraper.
This script updates the process_reddit_leads method to properly handle data from the web scraper.
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of a file."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{filepath}.bak_{timestamp}'
        shutil.copy2(filepath, backup_file)
        print(f"Created backup of {filepath} as {backup_file}")
        return True
    else:
        print(f"Error: {filepath} file not found!")
        return False

def fix_process_reddit_leads():
    """Fix the process_reddit_leads method in MessageGenerator to handle web scraper data."""
    message_generator_path = 'communication/message_generator.py'
    
    if not os.path.exists(message_generator_path):
        print(f"Error: {message_generator_path} not found!")
        return False
    
    # Backup the file
    backup_file(message_generator_path)
    
    try:
        with open(message_generator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the process_reddit_leads method in the MessageGenerator class
        process_method_pattern = r'def process_reddit_leads\(self, leads_data: List\[Dict\[str, Any\]\], max_leads: int = 10\)'
        process_method_match = re.search(process_method_pattern, content)
        
        if not process_method_match:
            print("Could not find process_reddit_leads method in MessageGenerator class!")
            # Try a more flexible search
            process_method_pattern = r'def process_reddit_leads\(self,'
            process_method_match = re.search(process_method_pattern, content)
            if not process_method_match:
                print("Could not find process_reddit_leads method with flexible search. Manual fix may be required.")
                return False
        
        process_method_idx = process_method_match.start()
        
        # Find the next method after process_reddit_leads
        next_method_idx = content.find("def ", process_method_idx + 1)
        if next_method_idx == -1:
            print("Could not find the end of process_reddit_leads method.")
            # Try to find the end in a different way - look for class end or file end
            class_end_idx = content.find("# Function to be imported", process_method_idx)
            if class_end_idx != -1:
                next_method_idx = class_end_idx
            else:
                # Use the end of file as a fallback
                next_method_idx = len(content)
        
        # Extract the process_reddit_leads method
        old_method = content[process_method_idx:next_method_idx]
        
        # Update for compatibility with web scraper data
        # We need to make sure it properly extracts context from post_content and handles different field names
        
        # Build the updated method - only changing specific parts
        new_method = old_method.replace(
            "# Extract context from post content",
            """# Extract context from post content
                # Web scraper provides 'post_content' directly, so we need to handle both formats
                context = ''
                if lead.get('post_content'):
                    context = lead.get('post_content', '')[:1000]
                elif lead.get('selftext'): # API format
                    context = lead.get('selftext', '')[:1000]"""
        )
        
        # Make sure matched_keywords is properly handled (web scraper uses this field)
        if "lead.get('matched_keywords'" not in new_method:
            new_method = new_method.replace(
                "lead['interests'] = lead.get('matched_keywords', '')",
                """# Handle both web scraper (matched_keywords) and API (matched_keywords) formats
                if isinstance(lead.get('matched_keywords'), list):
                    lead['interests'] = ', '.join(lead.get('matched_keywords', []))
                else:
                    lead['interests'] = lead.get('matched_keywords', '')"""
            )
        
        # Update the content with the new method
        new_content = content[:process_method_idx] + new_method + content[next_method_idx:]
        
        # Add a compatibility layer at the beginning of the method to normalize data
        compat_layer = """
            # Normalize web scraper data to ensure compatibility
            for lead in leads_data:
                # Ensure all necessary fields exist
                if 'post_title' not in lead and 'title' in lead:
                    lead['post_title'] = lead['title']
                if 'post_content' not in lead and 'selftext' in lead:
                    lead['post_content'] = lead['selftext']
                if 'username' not in lead and 'author' in lead:
                    lead['username'] = lead['author']
                if 'post_url' not in lead and 'url' in lead:
                    lead['post_url'] = lead['url']
            """
        
        # Insert the compatibility layer after the method signature
        method_sig_end = new_content.find(":", process_method_idx) + 1
        new_content = new_content[:method_sig_end] + compat_layer + new_content[method_sig_end:]
        
        # Write the updated content back to the file
        with open(message_generator_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✓ Fixed process_reddit_leads method in {message_generator_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing process_reddit_leads: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_generate_message():
    """Fix the generate_message method to handle different OpenAI response formats."""
    message_generator_path = 'communication/message_generator.py'
    
    if not os.path.exists(message_generator_path):
        print(f"Error: {message_generator_path} not found!")
        return False
    
    # Backup the file if not already backed up
    if not os.path.exists(f"{message_generator_path}.bak_"):
        backup_file(message_generator_path)
    
    try:
        with open(message_generator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the generate_message method
        generate_method_pattern = r'def generate_message\(self, lead_data: Dict\[str, Any\], retries: int = 3\)'
        generate_method_match = re.search(generate_method_pattern, content)
        
        if not generate_method_match:
            print("Could not find generate_message method with specific signature!")
            # Try a more flexible search
            generate_method_pattern = r'def generate_message\(self,'
            generate_method_match = re.search(generate_method_pattern, content)
            if not generate_method_match:
                print("Could not find generate_message method with flexible search. Manual fix may be required.")
                return False
        
        generate_method_idx = generate_method_match.start()
        
        # Find the next method after generate_message
        next_method_idx = content.find("def ", generate_method_idx + 1)
        if next_method_idx == -1:
            print("Could not find the end of generate_message method.")
            # Use the end of file as a fallback
            next_method_idx = len(content)
        
        # Extract the generate_message method
        old_method = content[generate_method_idx:next_method_idx]
        
        # Look for the response handling part
        response_handling_pattern = r'if self\.client_version == "v1":(.*?)else:(.*?)message = response\["choices"\]\[0\]\["message"\]\["content"\]\.strip\(\)'
        response_handling_match = re.search(response_handling_pattern, old_method, re.DOTALL)
        
        if not response_handling_match:
            print("Could not find the response handling code in generate_message method.")
            # Try to add the fix at a reasonable position instead
            
            # Look for a block that creates the response
            response_create_idx = old_method.find("response = self.client.chat.completions.create(")
            if response_create_idx == -1:
                response_create_idx = old_method.find("response = self.client.ChatCompletion.create(")
            
            if response_create_idx != -1:
                # Find where the response processing begins
                response_process_idx = old_method.find("message = ", response_create_idx)
                
                if response_process_idx != -1:
                    # Replace the old response processing logic
                    old_process_code = old_method[response_process_idx:].split('\n')[0]
                    
                    # Create the new code with improved response handling for all OpenAI SDK versions
                    new_process_code = """
                    # Handle response formats for different OpenAI SDK versions
                    try:
                        if self.client_version == "v1":
                            # Modern OpenAI SDK returns a Pydantic object
                            if hasattr(response.choices[0].message, 'content'):
                                message = response.choices[0].message.content.strip()
                            else:
                                # Alternate format for some SDK versions
                                message = response.choices[0]['message']['content'].strip()
                        else:
                            # Legacy API format (pre-1.0 versions)
                            message = response["choices"][0]["message"]["content"].strip()
                    except (AttributeError, KeyError, TypeError) as e:
                        # Fallback - try various formats if the expected one fails
                        logger.warning(f"Error extracting message from response: {e}")
                        try:
                            # Try treating as dict
                            if isinstance(response, dict):
                                message = response["choices"][0]["message"]["content"].strip()
                            # Try treating as object
                            elif hasattr(response, 'choices'):
                                if hasattr(response.choices[0].message, 'content'):
                                    message = response.choices[0].message.content.strip()
                                else:
                                    message = response.choices[0]['message']['content'].strip()
                            else:
                                # Last resort - stringified response
                                logger.error(f"Unknown response format: {response}")
                                message = str(response)
                        except Exception as e2:
                            logger.error(f"Failed all attempts to extract message: {e2}")
                            return None
                    """
                    
                    # Replace the old code with the new code
                    new_method = old_method.replace(old_process_code, new_process_code)
                    
                    # Update the content with the new method
                    new_content = content[:generate_method_idx] + new_method + content[next_method_idx:]
                    
                    # Write the updated content back to the file
                    with open(message_generator_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    print(f"✓ Fixed generate_message method in {message_generator_path}")
                    return True
        
        print("Could not find appropriate location to fix generate_message method. Manual fix may be required.")
        return False
        
    except Exception as e:
        print(f"Error fixing generate_message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fix the MessageGenerator compatibility issues."""
    print("==================================================")
    print("Fixing MessageGenerator Compatibility Issues")
    print("==================================================")
    
    # Fix process_reddit_leads method to handle web scraper data
    print("\n1. Fixing process_reddit_leads method...")
    process_method_success = fix_process_reddit_leads()
    
    # Fix generate_message method to handle different OpenAI response formats
    print("\n2. Fixing generate_message method for OpenAI response handling...")
    generate_method_success = fix_generate_message()
    
    # Print overall results
    print("\n==================================================")
    print("Fix Results:")
    print(f"- process_reddit_leads fix: {'✓ Passed' if process_method_success else '✗ Failed'}")
    print(f"- generate_message fix: {'✓ Passed' if generate_method_success else '✗ Failed'}")
    
    if process_method_success or generate_method_success:
        print("\nSome fixes were applied! Re-run the verification script to check if the downstream compatibility issue is resolved.")
    else:
        print("\nNo fixes were successfully applied. You may need to manually inspect and fix the MessageGenerator class.")
    
    print("\nNext steps:")
    print("1. Run the verification script again:")
    print("   python verification-script.py")
    print("2. Verify that the downstream compatibility test passes")
    print("==================================================")

if __name__ == "__main__":
    main()
