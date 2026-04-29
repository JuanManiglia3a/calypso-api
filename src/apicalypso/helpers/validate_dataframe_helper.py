"""
helpers/validate_dataframe_helper.py

Este módulo contiene la clase DataFrameValidator, que se encarga de validar un DataFrame de pandas contra un esquema definido en un modelo de datos.

Responsabilidades principales:
    - Validar la presencia de columnas requeridas en el DataFrame.
    - Verificar que no existan columnas adicionales no permitidas.
    - Comprobar que los tipos de datos de las columnas coincidan con los tipos esperados según el esquema.
"""


import pandas as pd
from pandas.api.types import (
    is_integer_dtype,
    is_float_dtype,
    is_bool_dtype,
    is_string_dtype,
    is_datetime64_any_dtype,
)
from datetime import datetime
from utils.logger import configure_logger

logger = configure_logger(name=__name__, level="INFO")

class DataFrameValidator:
    @staticmethod
    def _is_datetime_series(series: pd.Series) -> bool:
        """
        Acepta datetime en estas representaciones simples:
        - pandas datetime64
        - primer valor no nulo es pd.Timestamp o datetime
        """
        try:
            if is_datetime64_any_dtype(series):
                return True
        except Exception:
            pass

        # Fallback por inspección del primer valor válido
        try:
            first_valid_index = series.first_valid_index()
            if first_valid_index is not None:
                sample = series.loc[first_valid_index]
                if isinstance(sample, (pd.Timestamp, datetime)):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def validate(df: pd.DataFrame, schema):
        logger.info("Iniciando validación del DataFrame contra el esquema.")
        expected_fields = schema.model_fields.keys()
        missing = set(expected_fields) - set(df.columns)
        extra = set(df.columns) - set(expected_fields)
        if missing:
            logger.error(f"Faltan columnas requeridas: {missing}")
            raise ValueError(f"Faltan columnas requeridas: {missing}")
        if extra:
            logger.error(f"Columnas no permitidas en el archivo: {extra}")
            raise ValueError(f"Columnas no permitidas en el archivo: {extra}")
        for field, field_info in schema.model_fields.items():
            if field in df.columns:
                expected_type = field_info.annotation
                series = df[field]
                origin = getattr(expected_type, '__origin__', None)
                if origin is not None and origin is not type(None):
                    for t in expected_type.__args__:
                        if t is not type(None):
                            expected_type = t
                            break

                # Validación dtype-aware para soportar dtypes anulables (PyArrow Extension)
                if expected_type == int:
                    # Aceptar columnas enteras aun con nulos mezclados y floats que representen enteros
                    non_null = series.dropna()
                    if non_null.empty:
                        # Columna completamente nula: válida para entero
                        pass
                    elif is_integer_dtype(series):
                        # Tipos enteros puros, incluyendo Int64 anulable
                        pass
                    elif is_float_dtype(series):
                        # Aceptar si todos los no nulos son enteros “puros” (p.ej., 1.0, 2.0)
                        vals = pd.to_numeric(non_null, errors='coerce')
                        mask = pd.notna(vals)
                        if ((vals[mask] % 1) == 0).all():
                            pass
                        else:
                            logger.error(f"Columna '{field}' debe ser de tipo entero")
                            raise ValueError(f"Columna '{field}' debe ser de tipo entero")
                    elif str(series.dtype) == 'object':
                        # Object con mezcla de nulos y strings numéricos: validar que sean enteros
                        vals = pd.to_numeric(non_null, errors='coerce')
                        mask = pd.notna(vals)
                        if ((vals[mask] % 1) == 0).all():
                            pass
                        else:
                            logger.error(f"Columna '{field}' debe ser de tipo entero")
                            raise ValueError(f"Columna '{field}' debe ser de tipo entero")
                    else:
                        logger.error(f"Columna '{field}' debe ser de tipo entero")
                        raise ValueError(f"Columna '{field}' debe ser de tipo entero")
                elif expected_type == float:
                    if not is_float_dtype(series):
                        logger.error(f"Columna '{field}' debe ser de tipo flotante")
                        raise ValueError(f"Columna '{field}' debe ser de tipo flotante")
                elif expected_type == bool:
                    if not is_bool_dtype(series):
                        logger.error(f"Columna '{field}' debe ser de tipo booleano")
                        raise ValueError(f"Columna '{field}' debe ser de tipo booleano")
                elif expected_type == str:
                    # Aceptar columnas de texto con dtype 'string' o 'object', y columnas mixtas con nulos
                    non_null = series.dropna()
                    if non_null.empty:
                        # Si todos los valores son nulos, considerar válido para campo string
                        pass
                    elif is_string_dtype(series) or str(series.dtype) == 'object':
                        # string dtype moderno o object (texto heterogéneo)
                        pass
                    else:
                        logger.error(f"Columna '{field}' debe ser de tipo string")
                        raise ValueError(f"Columna '{field}' debe ser de tipo string")
                elif getattr(expected_type, "__name__", "") == "datetime" or expected_type is datetime:
                    if not DataFrameValidator._is_datetime_series(series):
                        logger.error(f"Columna '{field}' debe ser de tipo datetime")
                        raise ValueError(f"Columna '{field}' debe ser de tipo datetime")
        logger.info("Validación del DataFrame completada exitosamente.")
