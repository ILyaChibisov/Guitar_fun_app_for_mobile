# api/parser_client.py
"""
Клиент для работы с парсерами
Содержит все методы для управления парсерами (AMDM, MyTabs, AccordPro и т.д.)
"""
from kivy.logger import Logger
from api.client import api as base_api


class ParserClient:
    """Клиент для работы с парсерами"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._api = base_api

    def _get_headers(self):
        """Получить заголовки для запросов"""
        return self._api._get_headers(include_auth=True)

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None):
        """Выполнить запрос через основной API клиент"""
        return self._api._request(url, method, data, on_success, on_failure, include_auth=True)

    def _request_sync(self, url, method='GET', data=None):
        """Синхронный запрос"""
        return self._api._request_sync(url, method, data, include_auth=True)

    # ============ ОБЩИЕ МЕТОДЫ ============

    def get_active_parser_status(self, on_success=None, on_failure=None):
        """Получить статус активного парсера"""
        url = f"{self._api.config.API_BASE_URL}/parsers/active"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_active_parser_status_sync(self):
        """Получить статус активного парсера (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/active"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": True, "data": {"has_active_parser": False}}

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AMDM ============

    def start_amdm_parser(self, start_page, end_page, subdomain, on_success=None, on_failure=None):
        """Запустить парсер AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_amdm_parser_sync(self, start_page, end_page, subdomain):
        """Запустить парсер AMDM (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AMDM: {e}")
            return None

    def pause_amdm_parser(self, on_success=None, on_failure=None):
        """Поставить на паузу парсер AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/pause"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def pause_amdm_parser_sync(self):
        """Поставить на паузу парсер AMDM (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/pause"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка паузы парсера AMDM: {e}")
            return None

    def resume_amdm_parser(self, on_success=None, on_failure=None):
        """Возобновить парсер AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/resume"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def resume_amdm_parser_sync(self):
        """Возобновить парсер AMDM (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/resume"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка возобновления парсера AMDM: {e}")
            return None

    def stop_amdm_parser(self, on_success=None, on_failure=None):
        """Остановить парсер AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_amdm_parser_sync(self):
        """Остановить парсер AMDM (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AMDM: {e}")
            return None

    def get_amdm_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_amdm_parser_status_sync(self):
        """Получить статус парсера AMDM (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AMDM: {e}")
            return None

    def get_amdm_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из AMDM"""
        url = f"{self._api.config.API_BASE_URL}/parsers/amdm/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА MYTABS ============

    def start_mytabs_parser(self, start_page, end_page, subdomain, on_success=None, on_failure=None):
        """Запустить парсер MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_mytabs_parser_sync(self, start_page, end_page, subdomain):
        """Запустить парсер MyTabs (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера MyTabs: {e}")
            return None

    def pause_mytabs_parser(self, on_success=None, on_failure=None):
        """Поставить на паузу парсер MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/pause"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def pause_mytabs_parser_sync(self):
        """Поставить на паузу парсер MyTabs (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/pause"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка паузы парсера MyTabs: {e}")
            return None

    def resume_mytabs_parser(self, on_success=None, on_failure=None):
        """Возобновить парсер MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/resume"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def resume_mytabs_parser_sync(self):
        """Возобновить парсер MyTabs (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/resume"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка возобновления парсера MyTabs: {e}")
            return None

    def stop_mytabs_parser(self, on_success=None, on_failure=None):
        """Остановить парсер MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_mytabs_parser_sync(self):
        """Остановить парсер MyTabs (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера MyTabs: {e}")
            return None

    def get_mytabs_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_mytabs_parser_status_sync(self):
        """Получить статус парсера MyTabs (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера MyTabs: {e}")
            return None

    def get_mytabs_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из MyTabs"""
        url = f"{self._api.config.API_BASE_URL}/parsers/mytabs/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА ACCORDPRO ============

    def start_accord_pro_parser(self, start_group, end_group, on_success=None, on_failure=None):
        """Запустить парсер AccordPro"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_accord_pro_parser_sync(self, start_group, end_group):
        """Запустить парсер AccordPro (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AccordPro: {e}")
            return None

    def stop_accord_pro_parser(self, on_success=None, on_failure=None):
        """Остановить парсер AccordPro"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_accord_pro_parser_sync(self):
        """Остановить парсер AccordPro (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AccordPro: {e}")
            return None

    def get_accord_pro_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера AccordPro"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_accord_pro_parser_status_sync(self):
        """Получить статус парсера AccordPro (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AccordPro: {e}")
            return None

    def get_accord_pro_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из AccordPro"""
        url = f"{self._api.config.API_BASE_URL}/parsers/accordpro/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AKKORDUS ============

    def start_akkordus_parser(self, start_group, end_group, on_success=None, on_failure=None):
        """Запустить парсер Akkordus"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_akkordus_parser_sync(self, start_group, end_group):
        """Запустить парсер Akkordus (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Akkordus: {e}")
            return None

    def stop_akkordus_parser(self, on_success=None, on_failure=None):
        """Остановить парсер Akkordus"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_akkordus_parser_sync(self):
        """Остановить парсер Akkordus (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Akkordus: {e}")
            return None

    def get_akkordus_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера Akkordus"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_akkordus_parser_status_sync(self):
        """Получить статус парсера Akkordus (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Akkordus: {e}")
            return None

    def get_akkordus_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из Akkordus"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordus/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА MUZLAND ============

    def start_muzland_parser(self, start_group, end_group, on_success=None, on_failure=None):
        """Запустить парсер Muzland"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_muzland_parser_sync(self, start_group, end_group):
        """Запустить парсер Muzland (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Muzland: {e}")
            return None

    def stop_muzland_parser(self, on_success=None, on_failure=None):
        """Остановить парсер Muzland"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_muzland_parser_sync(self):
        """Остановить парсер Muzland (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Muzland: {e}")
            return None

    def get_muzland_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера Muzland"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_muzland_parser_status_sync(self):
        """Получить статус парсера Muzland (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Muzland: {e}")
            return None

    def get_muzland_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из Muzland"""
        url = f"{self._api.config.API_BASE_URL}/parsers/muzland/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА CHORDIE ============

    def start_chordie_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        """Запустить парсер Chordie"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_chordie_parser_sync(self, start_letter, end_letter):
        """Запустить парсер Chordie (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Chordie: {e}")
            return None

    def stop_chordie_parser(self, on_success=None, on_failure=None):
        """Остановить парсер Chordie"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_chordie_parser_sync(self):
        """Остановить парсер Chordie (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Chordie: {e}")
            return None

    def get_chordie_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера Chordie"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_chordie_parser_status_sync(self):
        """Получить статус парсера Chordie (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Chordie: {e}")
            return None

    def get_chordie_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из Chordie"""
        url = f"{self._api.config.API_BASE_URL}/parsers/chordie/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА 5LAD ============

    def start_fivelad_parser(self, start_group, end_group, on_success=None, on_failure=None):
        """Запустить парсер 5Lad"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_fivelad_parser_sync(self, start_group, end_group):
        """Запустить парсер 5Lad (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера 5Lad: {e}")
            return None

    def stop_fivelad_parser(self, on_success=None, on_failure=None):
        """Остановить парсер 5Lad"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_fivelad_parser_sync(self):
        """Остановить парсер 5Lad (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера 5Lad: {e}")
            return None

    def get_fivelad_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера 5Lad"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_fivelad_parser_status_sync(self):
        """Получить статус парсера 5Lad (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера 5Lad: {e}")
            return None

    def get_fivelad_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из 5Lad"""
        url = f"{self._api.config.API_BASE_URL}/parsers/fivelad/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AKKORDBARD ============

    def start_akkordbard_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        """Запустить парсер AkkordBard"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_akkordbard_parser_sync(self, start_letter, end_letter):
        """Запустить парсер AkkordBard (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AkkordBard: {e}")
            return None

    def stop_akkordbard_parser(self, on_success=None, on_failure=None):
        """Остановить парсер AkkordBard"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_akkordbard_parser_sync(self):
        """Остановить парсер AkkordBard (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AkkordBard: {e}")
            return None

    def get_akkordbard_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера AkkordBard"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_akkordbard_parser_status_sync(self):
        """Получить статус парсера AkkordBard (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AkkordBard: {e}")
            return None

    def get_akkordbard_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из AkkordBard"""
        url = f"{self._api.config.API_BASE_URL}/parsers/akkordbard/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА DOMHVE ============

    def start_domhve_parser(self, start_song, end_song, on_success=None, on_failure=None):
        """Запустить парсер Domhve"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/start"
        data = {"start_song": start_song, "end_song": end_song}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_domhve_parser_sync(self, start_song, end_song):
        """Запустить парсер Domhve (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/start"
        data = {"start_song": start_song, "end_song": end_song}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Domhve: {e}")
            return None

    def stop_domhve_parser(self, on_success=None, on_failure=None):
        """Остановить парсер Domhve"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_domhve_parser_sync(self):
        """Остановить парсер Domhve (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Domhve: {e}")
            return None

    def get_domhve_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера Domhve"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_domhve_parser_status_sync(self):
        """Получить статус парсера Domhve (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Domhve: {e}")
            return None

    def get_domhve_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из Domhve"""
        url = f"{self._api.config.API_BASE_URL}/parsers/domhve/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА RUSHSOUND ============

    def start_rushsound_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        """Запустить парсер RushSound"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure)

    def start_rushsound_parser_sync(self, start_letter, end_letter):
        """Запустить парсер RushSound (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self._api.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера RushSound: {e}")
            return None

    def stop_rushsound_parser(self, on_success=None, on_failure=None):
        """Остановить парсер RushSound"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure)

    def stop_rushsound_parser_sync(self):
        """Остановить парсер RushSound (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/stop"
        try:
            response = self._api.session.post(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера RushSound: {e}")
            return None

    def get_rushsound_parser_status(self, on_success=None, on_failure=None):
        """Получить статус парсера RushSound"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)

    def get_rushsound_parser_status_sync(self):
        """Получить статус парсера RushSound (синхронно)"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/status"
        try:
            response = self._api.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера RushSound: {e}")
            return None

    def get_rushsound_recent_songs(self, limit=10, on_success=None, on_failure=None):
        """Получить последние песни из RushSound"""
        url = f"{self._api.config.API_BASE_URL}/parsers/rushsound/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure)


# Создаем экземпляр клиента парсеров
parser_client = ParserClient()