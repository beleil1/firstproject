from fastapi import APIRouter, HTTPException, Depends
from models.model_message import FriendRequest, FriendAccept, Message
from db.mongo import connection
from schemas.auth_repo import authentication
from bson import ObjectId
from datetime import datetime
from typing import List, Dict
from bson import json_util
import json

router = APIRouter(prefix='/friends', tags=["Friends API"])


@router.get('/search_users', description="Search for users by prefix (minimum 3 characters).")
async def search_users(prefix: str, current_user=Depends(authentication.authenticate_token())) -> List[Dict[str, str]]:
    if len(prefix) < 3:
        raise HTTPException(
            status_code=400, detail="Search term must be at least 3 characters long")

    users_cursor = connection.site_database.users.find(
        {"username": {"$regex": f"^{prefix}"}},
        {"_id": 1, "username": 1}
    )

    users = await users_cursor.to_list(length=100)
    user_data = [{"id": str(user["_id"]), "username": user["username"]}
                 for user in users]

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return user_data


@router.post('/send', description="Send a friend request to a user by username.")
async def send_friend_request(request: FriendRequest, current_user=Depends(authentication.authenticate_token())):
    from_user_username = current_user["username"]
    from_user = await connection.site_database.users.find_one({"username": from_user_username})
    if not from_user:
        raise HTTPException(status_code=404, detail="From user not found")

    to_user = await connection.site_database.users.find_one({"username": request.to_user})
    if not to_user:
        raise HTTPException(status_code=404, detail="To user not found")

    existing_request = await connection.site_database.friend_requests.find_one(
        {"from_user": from_user["_id"], "to_user": to_user["_id"]})
    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="You have already sent a friend request to this user.")

    await connection.site_database.friend_requests.insert_one({"from_user": from_user["_id"], "to_user": to_user["_id"]})

    return {"detail": "Friend request sent"}


@router.get('/friend_requests', description="Get the list of friend requests received by the current user.")
async def get_friend_requests(current_user=Depends(authentication.authenticate_token())):
    user_id = ObjectId(current_user['id'])

    friend_requests = await connection.site_database.friend_requests.find(
        {"to_user": user_id}).to_list(length=100)

    friend_requests_with_username = []
    for request in friend_requests:
        from_user_id = request["from_user"]
        from_user = await connection.site_database.users.find_one({"_id": from_user_id})
        if from_user:
            request_with_username = {
                "request_id": str(request["_id"]),
                "from_user_id": str(from_user_id),
                "from_username": from_user.get("username", "Unknown")
            }
            friend_requests_with_username.append(request_with_username)

    if not friend_requests_with_username:
        raise HTTPException(status_code=404, detail="No friend requests found")

    return friend_requests_with_username


@router.put('/accept/{request_id}', description="Accept or reject a friend request.")
async def accept_friend_request(request_id: str, status: bool, current_user=Depends(authentication.authenticate_token())):
    friend_request = await connection.site_database.friend_requests.find_one({"_id": ObjectId(request_id)})
    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    await connection.site_database.friend_requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": status}})

    from_user = await connection.site_database.users.find_one({"_id": friend_request["from_user"]})
    to_user = await connection.site_database.users.find_one({"_id": friend_request["to_user"]})

    if status:
        await connection.site_database.users.update_one({"_id": from_user["_id"]}, {"$addToSet": {"friends": to_user["_id"]}})
        await connection.site_database.users.update_one({"_id": to_user["_id"]}, {"$addToSet": {"friends": from_user["_id"]}})

        message = f"Your friend request has been accepted by {current_user['username']}."
    else:
        message = f"Your friend request has been rejected by {current_user['username']}."

    return {"detail": "Friend request status updated", "message": message}


@router.get('/friends', description="Get the list of friends of the current user.")
async def get_friends(search_query: str = None, current_user=Depends(authentication.authenticate_token())):
    user = await connection.site_database.users.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if search_query:
        friends = await connection.site_database.users.find(
            {"_id": {"$in": user.get("friends", [])}, "username": {
                "$regex": search_query, "$options": "i"}},
            projection={"_id": 1, "username": 1}
        ).to_list(length=100)
    else:
        friends = await connection.site_database.users.find(
            {"_id": {"$in": user.get("friends", [])}},
            projection={"_id": 1, "username": 1}
        ).to_list(length=100)

    if not friends:
        raise HTTPException(status_code=404, detail="No friends found")

    return [{"id": str(friend["_id"]), "username": friend["username"]} for friend in friends]


@router.delete('/remove/{friend_username}', description="Remove a friend from your friend list by specifying their username.")
async def remove_friend(friend_username: str, current_user=Depends(authentication.authenticate_token())):
    user = await connection.site_database.users.find_one({"username": current_user["username"]})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    friend = await connection.site_database.users.find_one({"username": friend_username},
                                                           projection={"_id": 1, "username": 1})
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    await connection.site_database.users.update_one(
        {"_id": user["_id"]},
        {"$pull": {"friends": friend["_id"]}}
    )

    removed_friend_info = {
        "id": str(friend["_id"]),
        "username": friend["username"]
    }

    return {"detail": "Friend removed successfully", "friend": removed_friend_info}
