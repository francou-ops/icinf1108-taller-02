from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pets.pet_model import Pet as PetModel
from app.shared.exceptions import conflict
from app.students.student_model import Student as StudentModel
from app.students.students_schemas import (
    CreateStudentDto,
    Student,
    StudentList,
    UpdateStudentDto,
)


class StudentsService:
    def find_all(self, db: Session) -> StudentList:
        students = db.scalars(
            select(StudentModel).order_by(StudentModel.createdAt.desc())
        ).all()

        return StudentList(
            total=len(students),
            items=[Student.model_validate(s) for s in students],
        )

    def find_by_id(self, db: Session, student_id: str) -> Student:
        return Student.model_validate(self._get(db, student_id))

    def create(self, db: Session, data: CreateStudentDto) -> Student:
        self.assert_no_conflicts(db, data)

        student = StudentModel(
            id=str(uuid4()),
            name=data.name,
            username=data.username,
            email=data.email,
            age=data.age,
        )
        try:
            db.add(student)
            db.flush()
            db.commit()
        except IntegrityError as err:
            db.rollback()
            self._handle_integrity_error(err)
        except Exception:
            db.rollback()
            raise

        return Student.model_validate(student)

    def update(self, db: Session, student_id: str, data: UpdateStudentDto) -> Student:
        student = self._get(db, student_id)
        self.assert_no_conflicts(db, data, except_id=student_id)

        if data.name is not None:
            student.name = data.name
        if data.username is not None:
            student.username = data.username
        if data.email is not None:
            student.email = data.email
        if data.age is not None:
            student.age = data.age

        try:
            db.flush()
            db.commit()
        except IntegrityError as err:
            db.rollback()
            self._handle_integrity_error(err)
        except Exception:
            db.rollback()
            raise

        return Student.model_validate(student)

    def delete(self, db: Session, student_id: str) -> Student:
        student = self._get(db, student_id)
        result = Student.model_validate(student)

        try:
            db.execute(delete(PetModel).where(PetModel.studentId == student_id))
            db.delete(student)
            db.flush()
            db.commit()
        except Exception:
            db.rollback()
            raise

        return result

    def assert_no_conflicts(
        self,
        db: Session,
        data: CreateStudentDto | UpdateStudentDto,
        except_id: str | None = None,
    ) -> None:
        errors: dict[str, dict[str, str]] = {}

        if data.email:
            existing = db.scalar(
                select(StudentModel).where(StudentModel.email == data.email)
            )
            if existing and existing.id != except_id:
                errors["email"] = {"message": "El correo electrónico ya está en uso"}

        if data.username:
            existing = db.scalar(
                select(StudentModel).where(StudentModel.username == data.username)
            )
            if existing and existing.id != except_id:
                errors["username"] = {"message": "El nombre de usuario ya está en uso"}

        if errors:
            raise conflict(errors)

    def _handle_integrity_error(self, err: IntegrityError) -> None:
        sqlstate = getattr(err.orig, "sqlstate", None)
        diag = getattr(err.orig, "diag", None)
        constraint = getattr(diag, "constraint_name", None)
        fields = {
            "students_email_key": ("email", "El correo electrónico ya está en uso"),
            "students_username_key": (
                "username",
                "El nombre de usuario ya está en uso",
            ),
        }
        if sqlstate == "23505" and constraint in fields:
            field, message = fields[constraint]
            raise conflict({field: {"message": message}}) from err
        raise err

    def _get(self, db: Session, student_id: str) -> StudentModel:
        student = db.get(StudentModel, student_id)

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estudiante no encontrado",
            )

        return student


students_service = StudentsService()
