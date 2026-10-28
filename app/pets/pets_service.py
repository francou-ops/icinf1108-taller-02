from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pets.pet_model import Pet as PetModel
from app.pets.pets_schemas import CreatePetDto, Pet, PetList, UpdatePetDto
from app.shared.exceptions import conflict
from app.students.students_service import StudentsService, students_service


class PetsService:
    def __init__(self, students: StudentsService) -> None:
        self.students_service = students

    def find_all_for_student(self, db: Session, student_id: str) -> PetList:
        self.students_service.find_by_id(db, student_id)

        pets = db.scalars(
            select(PetModel)
            .where(PetModel.studentId == student_id)
            .order_by(PetModel.createdAt.desc())
        ).all()

        return PetList(total=len(pets), items=[Pet.model_validate(p) for p in pets])

    def create(self, db: Session, student_id: str, data: CreatePetDto) -> Pet:
        self.students_service.find_by_id(db, student_id)
        self.assert_no_conflicts(db, student_id, data)

        pet = PetModel(
            id=str(uuid4()),
            studentId=student_id,
            name=data.name,
            species=data.species,
            age=data.age,
        )
        try:
            db.add(pet)
            db.flush()
            db.commit()
        except IntegrityError as err:
            db.rollback()
            self._handle_integrity_error(err)
        except Exception:
            db.rollback()
            raise

        return Pet.model_validate(pet)

    def update(
        self, db: Session, student_id: str, pet_id: str, data: UpdatePetDto
    ) -> Pet:
        pet = self.find_owned(db, student_id, pet_id)
        self.assert_no_conflicts(db, student_id, data, except_id=pet_id)

        if data.name is not None:
            pet.name = data.name
        if data.species is not None:
            pet.species = data.species
        if data.age is not None:
            pet.age = data.age

        try:
            db.flush()
            db.commit()
        except IntegrityError as err:
            db.rollback()
            self._handle_integrity_error(err)
        except Exception:
            db.rollback()
            raise

        return Pet.model_validate(pet)

    def delete(self, db: Session, student_id: str, pet_id: str) -> Pet:
        pet = self.find_owned(db, student_id, pet_id)
        result = Pet.model_validate(pet)

        try:
            db.delete(pet)
            db.flush()
            db.commit()
        except Exception:
            db.rollback()
            raise

        return result

    def _handle_integrity_error(self, err: IntegrityError) -> None:
        sqlstate = getattr(err.orig, "sqlstate", None)
        diag = getattr(err.orig, "diag", None)
        constraint = getattr(diag, "constraint_name", None)
        if sqlstate == "23505" and constraint == "pets_studentId_name_key":
            raise conflict(
                {"name": {"message": "Ya tienes una mascota con ese nombre"}}
            ) from err
        raise err

    def find_owned(self, db: Session, student_id: str, pet_id: str) -> PetModel:
        self.students_service.find_by_id(db, student_id)

        pet = db.get(PetModel, pet_id)

        if pet is None or pet.studentId != student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mascota no encontrada",
            )

        return pet

    def assert_no_conflicts(
        self,
        db: Session,
        student_id: str,
        data: CreatePetDto | UpdatePetDto,
        except_id: str | None = None,
    ) -> None:
        if not data.name:
            return

        existing = db.scalar(
            select(PetModel).where(
                PetModel.studentId == student_id,
                PetModel.name == data.name,
            )
        )

        if existing and existing.id != except_id:
            raise conflict(
                {"name": {"message": "Ya tienes una mascota con ese nombre"}}
            )


pets_service = PetsService(students_service)
