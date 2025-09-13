import base64
import os

# Your uploaded photo as base64 (from the conversation)
# This is the photo you uploaded that shows the limitation

def save_user_photo():
    """Save the user's uploaded photo for testing"""
    
    # Note: In a real system, this would come from an upload endpoint
    # For now, let me create a simple way to save a test photo
    
    print("To test with your photo, please:")
    print("1. Save your photo as 'user_test_photo.jpg' in the attendance folder")
    print("2. Run: python test_user_photo.py user_test_photo.jpg")
    print("")
    print("This will test if the robust face recognition can identify you")
    print("(assuming you're one of the 5 students in the database)")

if __name__ == "__main__":
    save_user_photo()