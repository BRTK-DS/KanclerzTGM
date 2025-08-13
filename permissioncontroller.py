import json
from pathlib import Path
from enum import Enum

class ModuleName(Enum):
    MODERATOR = "moderator"
    ECONOMY = "ekonomia"
    LEVEL = "poziomy"

class PermissionController:
    def __init__(self, filepath="module_roles.json"):
        self.filepath = Path(filepath)
        self.roles_map = self._load_or_create()

    def _load_or_create(self):
        if not self.filepath.exists():
            self._save({})
            return {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        roles_map = {}
        for role_id, perms in data.items():
            roles_map[str(role_id)] = [ModuleName(p) for p in perms]
        return roles_map

    """Zapisuje roles_map do pliku"""
    def _save(self, data=None):
        if data is None:
            data = self.roles_map
        serializable_data = {
            role_id: [perm.value for perm in perms] for role_id, perms in data.items()
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=4)

    """Zwraca listę role_id, które mają dane uprawnienie (enum)"""
    def get_roles_with_permission(self, module: ModuleName) -> list[int]:
        result = []
        for role_id, perms in self.roles_map.items():
            if module in perms:
                result.append(int(role_id))
        return result

    """Dodaje uprawnienie dla roli"""
    def add_role_permission(self, role_id: str, module: ModuleName):
        role_id = str(role_id)
        if role_id not in self.roles_map:
            self.roles_map[role_id] = []
        if module not in self.roles_map[role_id]:
            self.roles_map[role_id].append(module)
        self._save()

    """Usuwa uprawnienie z roli"""
    def remove_role_permission(self, role_id: str, module: ModuleName):
        role_id = str(role_id)
        if role_id in self.roles_map and module in self.roles_map[role_id]:
            self.roles_map[role_id].remove(module)
            if not self.roles_map[role_id]:
                del self.roles_map[role_id]
            self._save()

    """Sprawdza, czy dana rola ma uprawnienie"""
    def has_permission(self, role_id: str, module: ModuleName) -> bool:
        role_id = str(role_id)
        return module in self.roles_map.get(role_id, [])

    """Zwraca listę wszystkich role_id"""
    def all_roles(self) -> list[int]:
        return [int(role_id) for role_id in self.roles_map.keys()]
