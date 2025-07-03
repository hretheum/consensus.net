#!/usr/bin/env python3
"""
Demonstration script for the enhanced OutputGenerator functionality.

This script shows all the new output processing capabilities.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.simple_agent import SimpleAgent, OutputGenerator

def main():
    print("=== Output Processing Module Demonstration ===\n")
    
    # Create an agent and get a verification result
    agent = SimpleAgent("demo_agent")
    result = agent.verify("The Earth is round.")
    
    print(f"Original result: {result}\n")
    
    # Initialize the output generator
    output_gen = OutputGenerator()
    
    print("=== 1. MULTIPLE OUTPUT FORMATS ===\n")
    
    print("--- TEXT FORMAT (Basic) ---")
    text_basic = output_gen.to_text_format(result)
    print(text_basic)
    print()
    
    print("--- TEXT FORMAT (Detailed) ---")
    text_detailed = output_gen.to_text_format(result, detailed=True)
    print(text_detailed)
    print()
    
    print("--- JSON FORMAT ---")
    json_output = output_gen.to_json_format(result, pretty=True)
    print(json_output)
    print()
    
    print("--- STRUCTURED FORMAT ---")
    structured = output_gen.to_structured_format(result)
    print(structured)
    print()
    
    print("=== 2. DELIVERY CHANNELS ===\n")
    
    print("--- API RESPONSE FORMAT ---")
    api_response = output_gen.format_for_api_response(result, format_type="json")
    print(api_response)
    print()
    
    print("--- MESSAGE QUEUE FORMAT (Standard) ---")
    queue_standard = output_gen.format_for_message_queue(result, queue_type="standard")
    print(queue_standard)
    print()
    
    print("--- MESSAGE QUEUE FORMAT (Compact) ---")
    queue_compact = output_gen.format_for_message_queue(result, queue_type="compact")
    print(queue_compact)
    print()
    
    print("=== 3. USER-FRIENDLY FORMAT ===\n")
    friendly = output_gen.format_user_friendly(result)
    print(friendly)
    print()
    
    print("=== 4. ERROR HANDLING ===\n")
    
    print("--- Handling Verification Error ---")
    error_result = output_gen.handle_verification_errors(ValueError("Simulated network error"))
    print("Error result:", error_result)
    print()
    
    print("--- Error Result in User-Friendly Format ---")
    error_friendly = output_gen.format_user_friendly(error_result)
    print(error_friendly)
    print()
    
    print("=== 5. QUALITY VALIDATION ===\n")
    
    # Test with different claims for different verdicts
    claims = [
        "The sky is blue.",
        "The Earth is flat.",
        "Some uncertain scientific claim about quantum mechanics.",
    ]
    
    for claim in claims:
        print(f"--- Processing: {claim} ---")
        result = agent.verify(claim)
        
        # Check quality
        is_quality = output_gen.validate_result_quality(result)
        print(f"Quality validation: {'PASS' if is_quality else 'FAIL'}")
        
        # Show user-friendly format
        friendly = output_gen.format_user_friendly(result)
        print(friendly)
        print()

if __name__ == "__main__":
    main()