import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *

def get_gemini_models():
    """
    Lấy danh sách các model Gemini có sẵn và phân loại theo version và type.
    
    Returns:
        dict: Dictionary chứa các danh sách model được phân loại:
            - flash_models_20: Gemini 2.0 Flash models
            - flash_models_25: Gemini 2.5 Flash models  
            - thinking_models_20: Gemini 2.0 Thinking models
            - thinking_models_25: Gemini 2.5 Thinking models
    """
    print("Đang lấy danh sách model...")

    available_models = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            if 'lite' not in model_name:
                available_models.append({
                    'model_name': model_name,
                })

    # Lọc và phân loại các model
    flash_models_20 = []
    flash_models_25 = []
    thinking_models_20 = []
    thinking_models_25 = []

    for model in available_models:
        model_name = model['model_name']
        
        # Gemini 2.0 models
        if 'gemini-2.0' in model_name:
            if 'thinking' in model_name:
                thinking_models_20.append(model_name)
            elif 'flash' in model_name:
                flash_models_20.append(model_name)
        
        # Gemini 2.5 models
        elif 'gemini-2.5' in model_name:
            if 'thinking' in model_name:
                thinking_models_25.append(model_name)
            elif 'flash' in model_name:
                flash_models_25.append(model_name)

    print("\n=== GEMINI 2.0 FLASH MODELS (NO LITE) ===")
    for model in sorted(flash_models_20):
        print(f"{model}")

    print("\n=== GEMINI 2.5 FLASH MODELS (NO LITE) ===")
    for model in sorted(flash_models_25):
        print(f"{model}")

    print("\n=== GEMINI 2.0 THINKING MODELS ===")
    for model in sorted(thinking_models_20):
        print(f"{model}")

    print("\n=== GEMINI 2.5 THINKING MODELS ===")
    for model in sorted(thinking_models_25):
        print(f"{model}")