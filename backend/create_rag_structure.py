#!/usr/bin/env python3
"""
Script to create the new RAG agent folder structure
"""

import os
from pathlib import Path

def create_folder_structure():
    """Create the complete RAG agent folder structure"""
    
    base_path = Path(".")
    
    # Define the folder structure
    folders = [
        # Agent core
        "src/agent",
        "src/core/retrieval",
        "src/core/llm", 
        "src/core/memory",
        "src/core/knowledge",
        "src/core/tools",
        
        # Infrastructure
        "src/infrastructure/vector_database",
        "src/infrastructure/monitoring", 
        "src/infrastructure/cache",
        
        # API
        "src/api",
        
        # Utils
        "src/utils",
        
        # Data
        "data/vector_store",
        "data/documents",
        "data/embeddings", 
        "data/conversations",
        
        # Config
        "config",
        
        # Tools
        "tools",
        
        # Tests
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/performance",
        
        # Notebooks
        "notebooks",
        
        # Docker
        "docker",
        
        # Scripts
        "scripts"
    ]
    
    # Create folders
    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py for Python packages
        if folder.startswith("src/"):
            init_file = folder_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# RAG Agent Package\n")
        
        print(f"✅ Created: {folder}")
    
    print(f"\n🎉 RAG Agent folder structure created successfully!")
    print(f"📁 Total folders created: {len(folders)}")

if __name__ == "__main__":
    create_folder_structure()