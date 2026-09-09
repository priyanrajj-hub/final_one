import os
import json

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def init_model():
    if not HAS_GENAI:
        return None
        
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        # Strip potential accidental backslash from copy-paste
        api_key = api_key.strip('\\').strip()
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash which is the standard fast model
        try:
            return genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
        except Exception as e:
            print(f"Error initializing generative model: {e}")
            return None
    return None

model = init_model()

def rule_based_fallback(sensor_data: dict) -> dict:
    """Provides a realistic fallback response if the LLM call fails."""
    # Basic rule logic
    ndvi = sensor_data.get("nNDVI", 0.5)
    capacitance = sensor_data.get("capacitance", 50)
    acoustic = sensor_data.get("acoustic_score", 10)
    
    stressor = "None"
    risk = "Low"
    action = "Continue normal monitoring."
    explanation = "Sensor readings are within typical healthy ranges."
    
    if ndvi < 0.4:
        stressor = "General Stress"
        risk = "High"
        action = "Inspect crop closely for anomalies."
        explanation = "NDVI is critically low, indicating poor plant health."
        
    if capacitance < 30:
        stressor = "Water-Stress"
        risk = "Medium to High"
        action = "Increase irrigation."
        explanation = "Soil capacitance is very low, suggesting inadequate moisture."
        
    if acoustic > 50:
        stressor = "Pest Infestation"
        risk = "High"
        action = "Activate acoustic deterrents and schedule manual inspection for pests."
        explanation = "High acoustic anomaly suggests possible pest activity."
        
    return {
        "risk_level": risk,
        "likely_stressor": stressor,
        "confidence_note": "Generated via rule-based fallback due to API unavailability.",
        "recommended_action": action,
        "explanation": explanation
    }

def get_advisory(sensor_data: dict) -> dict:
    if not model:
        print("Warning: GEMINI_API_KEY not found or model not initialized. Using fallback.")
        return rule_based_fallback(sensor_data)
        
    prompt = f"""
    You are an expert Agronomy AI. Analyze the following sensor data from a crop field 
    (ESP32-S3 ground node) and provide an advisory response.
    
    Sensor Data:
    {json.dumps(sensor_data, indent=2)}
    
    Provide your response in strictly valid JSON format matching this schema exactly:
    {{
        "risk_level": "Low | Medium | High",
        "likely_stressor": "e.g., Drought, Pests, Nutrient Deficiency, None",
        "confidence_note": "A short note on your confidence based on the data",
        "recommended_action": "Actionable advice for the farmer",
        "explanation": "Brief reasoning behind your advisory"
    }}
    """
    
    try:
        # Generate with JSON response forced by generation_config
        response = model.generate_content(prompt)
        advisory_text = response.text.strip()
        
        # In case the model still outputs markdown backticks, strip them
        if advisory_text.startswith("```json"):
            advisory_text = advisory_text[7:]
        if advisory_text.startswith("```"):
            advisory_text = advisory_text[3:]
        if advisory_text.endswith("```"):
            advisory_text = advisory_text[:-3]
            
        advisory = json.loads(advisory_text)
        
        # Verify required keys and provide default for any missing ones to prevent runtime crashes
        required_keys = ["risk_level", "likely_stressor", "confidence_note", "recommended_action", "explanation"]
        for k in required_keys:
            if k not in advisory:
                raise ValueError(f"Missing required key '{k}' in JSON response.")
                
        return advisory
    except Exception as e:
        print(f"LLM API Error: {str(e)}. Triggering rule-based fallback.")
        return rule_based_fallback(sensor_data)
