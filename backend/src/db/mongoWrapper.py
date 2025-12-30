from dotenv import load_dotenv
import os
import asyncio

from typing import Any, Dict, List, Optional
from pymongo import AsyncMongoClient

class Mongo_wrapper:

  def __init__(self, uri: str, AsyncMongoClient: str):
    self.uri = uri
    self.db_name = AsyncMongoClient
    self.client: Optional[AsyncMongoClient] = None
    self.db = None

  async def connect(self) -> None:
    """
    Initialize the client once and reuse it.
    """
    if self.client is None:
      self.client = AsyncMongoClient(self.uri)
      self.db = self.client[self.db_name]

  def collection(self, name: str):
    if self.db is None:
      raise RuntimeError("Database not connected. Call connect() first.")
    return self.db[name]

  async def insert_one(self, collection: str, doc: Dict[str, Any]) -> str:
    col = self.collection(collection)
    result = await col.insert_one(doc)
    return str(result.inserted_id)

  async def insert_many(self, collection: str, docs: List[Dict[str, Any]]) -> List[str]:
    col = self.collection(collection)
    result = await col.insert_many(docs)
    return [str(_id) for _id in result.inserted_ids]

  async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    col = self.collection(collection)
    return await col.find_one(query)

  async def find_many(
    self, collection: str,
    query: Dict[str, Any],
    limit: Optional[int] = None
  ) -> List[Dict[str, Any]]:
    col = self.collection(collection)
    cursor = col.find(query)
    return await cursor.to_list(length=limit)

  async def update_one(
    self,
    collection: str,
    query: Dict[str, Any],
    update_data: Dict[str, Any],
    raw: bool = False
) -> int:
    col = self.collection(collection)

    if raw:
        # Use MongoDB operators directly ($unset, $push, etc.)
        result = await col.update_one(query, update_data)
    else:
        # Default behavior: $set
        result = await col.update_one(query, {"$set": update_data})

    return result.modified_count


  async def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
    col = self.collection(collection)
    result = await col.delete_one(query)
    return result.deleted_count

    # ---------- EXTRA UTILITIES ---------- #

  async def count(self, collection: str, query: Dict[str, Any]) -> int:
    col = self.collection(collection)
    return await col.count_documents(query)

  async def drop_collection(self, collection: str) -> None:
    await self.collection(collection).drop()

mongo: Optional[Mongo_wrapper] = None

async def getMongo() -> Mongo_wrapper:
  global mongo

  if mongo is None:
    load_dotenv(".env")

    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB")
    
    if not uri or not db_name:
      raise ValueError("MONGO_URI and MONGO_DB must be set in environment variables")
    
    mongo = Mongo_wrapper(uri, db_name)
    await mongo.connect()

  return mongo


async def main():
  print("ping test for mongodb connection")
  mongo = await getMongo()

  try:
    await mongo.client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
  except Exception as e:
    print(e)

if __name__ == "__main__" :
  asyncio.run(main())

