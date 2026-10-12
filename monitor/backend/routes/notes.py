from flask import Blueprint, request
from repositories.notes import create_note, delete_note, find_note, list_notes, update_note
from rules import validate_note
from auth_helpers import api_access_error

notes_bp = Blueprint("notes", __name__, url_prefix="/api/notes")


@notes_bp.before_request
def require_operator():
    return api_access_error()


@notes_bp.get("")
def index():
    return {"notes": list_notes()}


@notes_bp.get("/<int:note_id>")
def detail(note_id):
    note = find_note(note_id)
    if note is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"note": note}


@notes_bp.post("")
def create():
    values, error = validate_note(request.get_json(silent=True))
    if error:
        return {"error": error}, 400
    return {"note": create_note(**values)}, 201


@notes_bp.put("/<int:note_id>")
def update(note_id):
    existing = find_note(note_id)
    if existing is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    values, error = validate_note(request.get_json(silent=True), default_status=existing["status"])
    if error:
        return {"error": error}, 400
    note = update_note(note_id, **values)
    if note is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"note": note}


@notes_bp.delete("/<int:note_id>")
def delete(note_id):
    if delete_note(note_id) is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"message": "메모를 삭제했습니다."}
