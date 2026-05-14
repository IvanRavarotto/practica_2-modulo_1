import pandas as pd
import requests
import tempfile
import os
from app.database import SessionLocal, engine
from app.models import Base, Question

DATASET_URL = "https://huggingface.co/datasets/stanfordnlp/web_questions/resolve/main/data/train-00000-of-00001.parquet"


def download_parquet(url: str) -> str:
    print(f"Descargando {url}...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


def sample_questions() -> pd.DataFrame:
    print("No se pudo descargar el dataset remoto. Usando datos de ejemplo locales.")
    return pd.DataFrame([
        {
            "question": "¿Cuál es la capital de Francia?",
            "answer": "París",
            "category": "Geografía",
            "source": "ejemplo",
        },
        {
            "question": "¿Qué lenguaje de programación se usa para FastAPI?",
            "answer": "Python",
            "category": "Programación",
            "source": "ejemplo",
        },
        {
            "question": "¿Qué base de datos usamos en este ejercicio?",
            "answer": "PostgreSQL",
            "category": "Bases de datos",
            "source": "ejemplo",
        },
    ])


def load_questions():
    Base.metadata.create_all(bind=engine)

    try:
        parquet_path = download_parquet(DATASET_URL)
        df = pd.read_parquet(parquet_path)
        os.unlink(parquet_path)
    except Exception as e:
        print(f"Advertencia: no se pudo cargar el dataset remoto: {e}")
        df = sample_questions()

    print(f"Columnas disponibles: {list(df.columns)}")
    print(f"Filas: {len(df)}")
    print(df.head(3))

    session = SessionLocal()
    try:
        for _, row in df.iterrows():
            question = Question(
                question=row.get("question", ""),
                answer=row.get("answer", "") or row.get("answer_alias", ""),
                category=row.get("category", None),
                source=row.get("source", None),
            )
            session.add(question)

        session.commit()
        print(f"Se insertaron {len(df)} preguntas correctamente.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    load_questions()
