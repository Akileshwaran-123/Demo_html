from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/library_system"
mongo = PyMongo(app)

# Convert ObjectId to string for JSON serialization
def parse_json(data):
    if isinstance(data, list):
        return [parse_json(item) for item in data]
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
        return data
    return data

@app.route('/')
def index():
    return render_template('index.html')

# Get all books
@app.route('/api/books', methods=['GET'])
def get_books():
    books = list(mongo.db.books.find())
    return jsonify(parse_json(books))

# Get a specific book
@app.route('/api/books/<book_id>', methods=['GET'])
def get_book(book_id):
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    if book:
        return jsonify(parse_json(book))
    return jsonify({"error": "Book not found"}), 404

# Create a new book
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'author', 'isbn', 'genre', 'published_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Convert published_date string to datetime object
    try:
        data['published_date'] = datetime.strptime(data['published_date'], '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    result = mongo.db.books.insert_one(data)
    
    # Return the created book with its id
    new_book = mongo.db.books.find_one({"_id": result.inserted_id})
    return jsonify(parse_json(new_book)), 201

# Update a book
@app.route('/api/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    
    # Check if book exists
    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    # Convert published_date string to datetime object if present
    if 'published_date' in data:
        try:
            data['published_date'] = datetime.strptime(data['published_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Update the book
    mongo.db.books.update_one({"_id": ObjectId(book_id)}, {"$set": data})
    
    # Return the updated book
    updated_book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return jsonify(parse_json(updated_book))

# Delete a book
@app.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    result = mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    
    if result.deleted_count == 0:
        return jsonify({"error": "Book not found"}), 404
    
    return jsonify({"message": "Book deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True)