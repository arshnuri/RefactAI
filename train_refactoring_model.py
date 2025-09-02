#!/usr/bin/env python3
"""
Model Training Script for Nested If Refactoring

This script fine-tunes a language model on synthetic refactoring data
to improve the quality of automated code transformations.
"""

import json
import os
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from datasets import Dataset
from typing import List, Dict, Any
import logging
from datetime import datetime
import numpy as np
from sklearn.model_selection import train_test_split

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefactoringDataProcessor:
    """Process synthetic refactoring data for model training"""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.examples = []
        self.tokenizer = None
        
    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load synthetic refactoring dataset"""
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.examples = data['examples']
        logger.info(f"Loaded {len(self.examples)} training examples")
        return self.examples
    
    def create_training_prompts(self) -> List[str]:
        """Create training prompts in instruction-following format"""
        prompts = []
        
        for example in self.examples:
            # Create instruction-following format
            prompt = f"""### Instruction:
Refactor the following {example['language']} code to reduce nested if statements using the {example['pattern']} pattern. The goal is to improve readability and reduce complexity.

### Input Code:
```{example['language']}
{example['original_code']}
```

### Expected Output:
```{example['language']}
{example['refactored_code']}
```

### Explanation:
{example['description']}
Complexity reduction: {example['complexity_reduction']}
Depth reduction: {example['depth_reduction']}
"""
            prompts.append(prompt)
        
        return prompts
    
    def create_simple_prompts(self) -> List[str]:
        """Create simple before/after prompts for training"""
        prompts = []
        
        for example in self.examples:
            # Simple format: Original -> Refactored
            prompt = f"""// Original nested code:
{example['original_code']}

// Refactored using {example['pattern']}:
{example['refactored_code']}"""
            prompts.append(prompt)
        
        return prompts
    
    def tokenize_data(self, prompts: List[str], tokenizer, max_length: int = 1024):
        """Tokenize training data"""
        def tokenize_function(examples):
            return tokenizer(
                examples['text'],
                truncation=True,
                padding=True,
                max_length=max_length,
                return_tensors="pt"
            )
        
        # Create dataset
        dataset = Dataset.from_dict({"text": prompts})
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        return tokenized_dataset

class RefactoringModelTrainer:
    """Train a model for code refactoring"""
    
    def __init__(self, model_name: str = "microsoft/CodeGPT-small-py"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def setup_model(self):
        """Initialize tokenizer and model"""
        logger.info(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        logger.info(f"Model loaded on device: {self.device}")
        
    def train_model(self, train_dataset, eval_dataset, output_dir: str):
        """Train the model on refactoring data"""
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            logging_steps=50,
            save_steps=500,
            eval_steps=500,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb
            dataloader_pin_memory=False,
            fp16=torch.cuda.is_available(),
            learning_rate=5e-5,
            weight_decay=0.01,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # Causal LM, not masked LM
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Train the model
        logger.info("Starting training...")
        trainer.train()
        
        # Save the final model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Training completed. Model saved to: {output_dir}")
        
        return trainer
    
    def evaluate_model(self, test_examples: List[Dict[str, Any]], output_file: str = None):
        """Evaluate the trained model on test examples"""
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call setup_model() first.")
        
        results = []
        
        for i, example in enumerate(test_examples[:10]):  # Test on first 10 examples
            # Create evaluation prompt
            prompt = f"""### Instruction:
Refactor the following {example['language']} code to reduce nested if statements.

### Input Code:
```{example['language']}
{example['original_code']}
```

### Refactored Code:
```{example['language']}
"""
            
            # Generate refactoring
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=300,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_refactoring = generated_text[len(prompt):].strip()
            
            result = {
                "example_id": i,
                "language": example['language'],
                "original_pattern": example['pattern'],
                "original_code": example['original_code'],
                "expected_refactoring": example['refactored_code'],
                "generated_refactoring": generated_refactoring,
                "expected_complexity_reduction": example['complexity_reduction'],
                "expected_depth_reduction": example['depth_reduction']
            }
            
            results.append(result)
            logger.info(f"Evaluated example {i+1}/10")
        
        # Save results
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Evaluation results saved to: {output_file}")
        
        return results

def main():
    """Main training pipeline"""
    print("🚀 Starting Refactoring Model Training Pipeline")
    
    # Configuration
    dataset_path = "synthetic_refactoring_dataset_20250731_151053.json"
    model_name = "microsoft/CodeGPT-small-py"  # Smaller model for faster training
    output_dir = f"./refactoring_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Check if dataset exists
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        print("Please run synthetic_data_generator.py first to create training data.")
        return
    
    # Step 1: Load and process data
    print("📊 Loading and processing training data...")
    processor = RefactoringDataProcessor(dataset_path)
    examples = processor.load_dataset()
    
    # Create training prompts
    prompts = processor.create_training_prompts()
    print(f"✅ Created {len(prompts)} training prompts")
    
    # Step 2: Setup model
    print("🤖 Setting up model and tokenizer...")
    trainer = RefactoringModelTrainer(model_name)
    
    try:
        trainer.setup_model()
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("Falling back to a smaller model...")
        trainer = RefactoringModelTrainer("gpt2")  # Fallback to GPT-2
        trainer.setup_model()
    
    # Step 3: Prepare datasets
    print("🔄 Tokenizing data and creating train/eval splits...")
    
    # Split data
    train_prompts, eval_prompts = train_test_split(prompts, test_size=0.2, random_state=42)
    
    # Tokenize
    train_dataset = processor.tokenize_data(train_prompts, trainer.tokenizer)
    eval_dataset = processor.tokenize_data(eval_prompts, trainer.tokenizer)
    
    print(f"📈 Training set: {len(train_dataset)} examples")
    print(f"📊 Evaluation set: {len(eval_dataset)} examples")
    
    # Step 4: Train model
    print("🎯 Starting model training...")
    
    try:
        trained_model = trainer.train_model(train_dataset, eval_dataset, output_dir)
        print("✅ Training completed successfully!")
        
        # Step 5: Evaluate model
        print("🔍 Evaluating trained model...")
        eval_examples = examples[:20]  # Use first 20 examples for evaluation
        eval_file = f"model_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results = trainer.evaluate_model(eval_examples, eval_file)
        
        print(f"📋 Evaluation completed. Results saved to: {eval_file}")
        print(f"🎉 Model training pipeline completed successfully!")
        
        # Print summary
        print("\n📊 Training Summary:")
        print(f"  • Model: {model_name}")
        print(f"  • Training examples: {len(train_dataset)}")
        print(f"  • Evaluation examples: {len(eval_dataset)}")
        print(f"  • Output directory: {output_dir}")
        print(f"  • Evaluation results: {eval_file}")
        
        print("\n🚀 Next Steps:")
        print("  1. Review evaluation results for quality")
        print("  2. Test model on real-world code examples")
        print("  3. Integrate trained model into RefactAI system")
        print("  4. Set up continuous learning pipeline")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        print("This might be due to insufficient GPU memory or other resource constraints.")
        print("Consider using a smaller model or reducing batch size.")
        
        # Provide alternative approach
        print("\n💡 Alternative Approach:")
        print("  • Use the synthetic dataset to improve rule-based refactoring")
        print("  • Extract patterns from successful refactorings")
        print("  • Implement template-based transformations")
        print("  • Use the data for few-shot prompting with existing LLMs")

if __name__ == "__main__":
    main()