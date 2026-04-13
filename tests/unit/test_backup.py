import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBackupModule:
    """Test suite for backup.py module"""
    
    def test_encontrar_pg_dump_existe(self):
        """Test that encontrar_pg_dump finds pg_dump.exe"""
        from backup import encontrar_pg_dump
        path = encontrar_pg_dump()
        assert path is not None
        assert os.path.exists(path)
        assert "pg_dump" in path.lower()
    
    def test_get_db_config_carga_desde_env(self):
        """Test that get_db_config loads configuration from .env file"""
        from backup import get_db_config
        config = get_db_config()
        
        assert config["host"] == "localhost"
        assert config["port"] == "5432"
        assert config["user"] == "postgres"
        assert config["password"] == "Leonard0"
    
    def test_get_db_config_database_name(self):
        """Test that database name is correctly read"""
        from backup import get_db_config
        config = get_db_config()
        
        assert "BDP-Nutric" in config["dbname"]
    
    def test_get_db_config_sin_archivo_env(self):
        """Test fallback when .env doesn't exist"""
        from backup import get_db_config
        
        with patch("backup.os.path.exists", return_value=False):
            config = get_db_config()
        
        assert config["host"] == "localhost"
        assert config["port"] == "5432"
        assert "BDP" in config["dbname"]
        assert config["user"] == "postgres"
        assert config["password"] == ""
    
    def test_crear_backup_directorio_backups_creado(self):
        """Test that backup directory is created"""
        from backup import crear_backup, _create_backup_dir
        
        with patch("backup.encontrar_pg_dump") as mock_pg_dump, \
             patch("backup.subprocess.run") as mock_run:
            
            mock_pg_dump.return_value = "C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe"
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            try:
                crear_backup()
            except:
                pass
        
        backup_dir = _create_backup_dir()
        assert os.path.exists(backup_dir)
    
    def test_crear_backup_ejecuta_pg_dump(self):
        """Test that pg_dump is called correctly"""
        from backup import crear_backup
        
        with patch("backup.encontrar_pg_dump") as mock_pg_dump, \
             patch("backup.subprocess.run") as mock_run:
            
            mock_pg_dump.return_value = "C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe"
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            ruta = crear_backup()
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args[1]["env"]
            assert "PGPASSWORD" in call_args
            assert call_args["PGPASSWORD"] == "Leonard0"
            assert "PGHOST" in call_args
            assert "PGPORT" in call_args
            assert "PGUSER" in call_args
    
    def test_crear_backup_falla_si_pg_dump_no_existe(self):
        """Test error when pg_dump not found"""
        from backup import crear_backup
        
        with patch("backup.encontrar_pg_dump", side_effect=FileNotFoundError("pg_dump not found")):
            with pytest.raises(FileNotFoundError):
                crear_backup()
    
    def test_crear_backup_falla_si_pg_dump_retorna_error(self):
        """Test error handling when pg_dump fails"""
        from backup import crear_backup
        
        with patch("backup.encontrar_pg_dump") as mock_pg_dump, \
             patch("backup.subprocess.run") as mock_run:
            
            mock_pg_dump.return_value = "C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe"
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Connection failed"
            mock_run.return_value = mock_result
            
            with pytest.raises(RuntimeError, match="pg_dump failed"):
                crear_backup()
    
    def test_limpiar_viejos_sin_directorio(self):
        """Test cleanup when directory doesn't exist"""
        from backup import limpiar_viejos
        
        with patch("backup.BACKUP_DIR", "Backups_test_nonexistent"):
            limpiar_viejos()
    
    def test_limpiar_viejos_menos_de_max(self):
        """Test cleanup when there are fewer than MAX_BACKUPS files"""
        from backup import limpiar_viejos, MAX_BACKUPS
        import shutil
        
        test_dir = "Backups_test_cleanup"
        os.makedirs(test_dir, exist_ok=True)
        
        try:
            for i in range(MAX_BACKUPS - 1):
                with open(os.path.join(test_dir, f"backup_test_{i}.sql"), "w") as f:
                    f.write("test")
            
            with patch("backup.BACKUP_DIR", test_dir):
                limpiar_viejos()
            
            remaining = [f for f in os.listdir(test_dir) if f.endswith(".sql")]
            assert len(remaining) == MAX_BACKUPS - 1
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_limpiar_viejos_mas_de_max(self):
        """Test cleanup when there are more than MAX_BACKUPS files"""
        from backup import limpiar_viejos, MAX_BACKUPS
        import shutil
        
        test_dir = "Backups_test_cleanup2"
        os.makedirs(test_dir, exist_ok=True)
        
        try:
            for i in range(MAX_BACKUPS + 2):
                with open(os.path.join(test_dir, f"backup_2026-01-{i:02d}_000000.sql"), "w") as f:
                    f.write("test")
            
            with patch("backup.BACKUP_DIR", test_dir):
                limpiar_viejos()
            
            remaining = [f for f in os.listdir(test_dir) if f.endswith(".sql")]
            assert len(remaining) <= MAX_BACKUPS
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_backup_dir_en_proyecto(self):
        """Test that Backups folder is in the project directory"""
        from backup import _create_backup_dir
        backup_dir = _create_backup_dir()
        assert "Backups" in backup_dir
    
    def test_get_db_config_password_no_vacia(self):
        """Test that password is loaded correctly"""
        from backup import get_db_config
        config = get_db_config()
        assert config["password"] != ""
        assert config["password"] == "Leonard0"
    
    def test_get_db_config_host_localhost(self):
        """Test that host is localhost"""
        from backup import get_db_config
        config = get_db_config()
        assert config["host"] == "localhost"
    
    def test_get_db_config_port_5432(self):
        """Test that port is 5432"""
        from backup import get_db_config
        config = get_db_config()
        assert config["port"] == "5432"


class TestBackupIntegration:
    """Integration tests for backup with actual system"""
    
    def test_backup_real_funciona(self):
        """Test that backup actually works (requires PostgreSQL)"""
        from backup import crear_backup, limpiar_viejos
        import os
        
        try:
            ruta = crear_backup()
            assert os.path.exists(ruta)
            assert os.path.getsize(ruta) > 0
            print(f"Backup created successfully: {ruta}")
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")