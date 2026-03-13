from database.mongo import jobs_collection

jobs_collection.insert_one({
    "test": "hello"
})

print("Inserted")