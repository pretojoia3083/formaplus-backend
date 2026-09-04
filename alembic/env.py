import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import Base, engine
from app.models import *

target_metadata = Base.metadata
