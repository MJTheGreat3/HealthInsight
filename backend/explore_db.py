#!/usr/bin/env python3
"""
Script to explore database structure and examine sample data
"""

import asyncio
import json
from src.db.mongoWrapper import getMongo

async def explore_database():
    print("🔍 Exploring Database Structure\n")
    
    # Connect to database
    mongo = await getMongo()
    
    # 1. Check what collections exist
    print("📋 Available Collections:")
    collections = await mongo.db.list_collection_names()
    for collection in collections:
        count = await mongo.count(collection, {})
        print(f"  - {collection}: {count} documents")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Look at sample entries in Reports collection
    if "Reports" in collections:
        print("📄 Sample Reports Collection Entries:")
        reports = await mongo.find_many("Reports", {}, limit=3)
        
        for i, report in enumerate(reports, 1):
            print(f"\n--- Report {i} ---")
            print(f"ID: {report.get('_id')}")
            print(f"Keys: {list(report.keys())}")
            
            # Show key fields
            for key in ['patientId', 'hospitalId', 'reportType', 'uploadedAt']:
                if key in report:
                    print(f"{key}: {report[key]}")
            
            # Show Attributes field structure
            if 'Attributes' in report:
                print(f"\nAttributes field:")
                attrs = report['Attributes']
                if isinstance(attrs, dict):
                    print(f"  Type: dict with {len(attrs)} keys")
                    for attr_key, attr_value in list(attrs.items())[:5]:  # Show first 5
                        if isinstance(attr_value, (str, int, float, bool)):
                            print(f"  {attr_key}: {attr_value}")
                        else:
                            print(f"  {attr_key}: {type(attr_value)} (value omitted)")
                    if len(attrs) > 5:
                        print(f"  ... and {len(attrs) - 5} more keys")
                else:
                    print(f"  Type: {type(attrs)}")
                    print(f"  Value: {str(attrs)[:200]}...")
            
            print("-" * 30)
    
    print("\n" + "="*50 + "\n")
    
    # 3. Check LLMReports collection
    if "LLMReports" in collections:
        print("🤖 Sample LLMReports Collection Entries:")
        llm_reports = await mongo.find_many("LLMReports", {}, limit=2)
        
        for i, llm_report in enumerate(llm_reports, 1):
            print(f"\n--- LLM Report {i} ---")
            print(f"ID: {llm_report.get('_id')}")
            print(f"Keys: {list(llm_report.keys())}")
            
            # Show key fields
            for key in ['reportId', 'analysis', 'createdAt']:
                if key in llm_report:
                    value = llm_report[key]
                    if isinstance(value, str) and len(value) > 100:
                        print(f"{key}: {value[:100]}...")
                    else:
                        print(f"{key}: {value}")
            
            print("-" * 30)
    else:
        print("🤖 LLMReports collection not found")
    
    print("\n" + "="*50 + "\n")
    
    # 4. Check other collections
    other_collections = [col for col in collections if col not in ["Reports", "LLMReports"]]
    if other_collections:
        print("📦 Other Collections (sample):")
        for collection in other_collections:
            print(f"\n--- {collection} ---")
            sample = await mongo.find_one(collection, {})
            if sample:
                print(f"Keys: {list(sample.keys())}")
                # Show a few key-value pairs
                for key, value in list(sample.items())[:3]:
                    if isinstance(value, str) and len(value) > 100:
                        print(f"{key}: {value[:100]}...")
                    else:
                        print(f"{key}: {value}")
            else:
                print("Collection is empty")

if __name__ == "__main__":
    asyncio.run(explore_database())