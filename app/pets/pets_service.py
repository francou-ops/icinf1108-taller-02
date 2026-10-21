from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, select
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
        db.add(pet)
        db.commit()

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

        db.commit()

        return Pet.model_validate(pet)

    def delete(self, db: Session, student_id: str, pet_id: str) -> Pet:
        pet = self.find_owned(db, student_id, pet_id)
        result = Pet.model_validate(pet)

        db.delete(pet)
        db.commit()

        return result

    def delete_all_for_student(self, db: Session, student_id: str) -> None:
        db.execute(delete(PetModel).where(PetModel.studentId == student_id))
        db.commit()

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
