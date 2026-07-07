# screens/manager.py
from kivy.uix.screenmanager import ScreenManager, NoTransition
from config.logger_config import get_logger
from .home_screen import HomeScreen
from .songs_screen import SongsScreen
from .chords_screen import ChordsScreen
from .dictionary_screen import DictionaryScreen
from .tuner_screen import TunerScreen
from .metronome_screen import MetronomeScreen
from .favorites_screen import FavoritesScreen
from .profile_screen import ProfileScreen
from .song_detail_screen import SongDetailScreen
from .admin_screen import AdminScreen
from .search_screen import SearchScreen
from .parsers_screens.amdm_parser_screen import AMDMParserScreen
from .parsers_screens.mytabs_parser_screen import MyTabsParserScreen
from .parsers_screens.accord_pro_parser_screen import AccordProParserScreen
from .parsers_screens.akkordus_parser_screen import AkkordusParserScreen
from .parsers_screens.muzland_parser_screen import MuzlandParserScreen
from .parsers_screens.chordie_parser_screen import ChordieParserScreen
from .parsers_screens.fivelad_parser_screen import FiveLadParserScreen
from .parsers_screens.akkordbard_parser_screen import AkkordBardParserScreen
from .parsers_screens.domhve_parser_screen import DomhveParserScreen
from .parsers_screens.rushsound_parser_screen import RushSoundParserScreen
from .term_detail_screen import TermDetailScreen

# ============ НОВЫЕ ЭКРАНЫ ============
from .settings_screen import SettingsScreen
from .help_screen import HelpScreen
from .promo_screen import PromoScreen
from .feedback_screen import FeedbackScreen

logger = get_logger('ScreenManager')


def setup_screen_manager():
    sm = ScreenManager(transition=NoTransition())

    sm.add_widget(HomeScreen(name='home'))
    sm.add_widget(SongsScreen(name='songs'))
    sm.add_widget(ChordsScreen(name='chords'))
    sm.add_widget(DictionaryScreen(name='dictionary'))
    sm.add_widget(TunerScreen(name='tuner'))
    sm.add_widget(MetronomeScreen(name='metronome'))
    sm.add_widget(FavoritesScreen(name='favorites'))
    sm.add_widget(ProfileScreen(name='profile'))
    sm.add_widget(SongDetailScreen(name='song_detail'))
    sm.add_widget(AdminScreen(name='admin'))
    sm.add_widget(SearchScreen(name='search'))
    sm.add_widget(TermDetailScreen(name='term_detail'))

    # ============ НОВЫЕ ЭКРАНЫ ============
    sm.add_widget(SettingsScreen(name='settings'))
    sm.add_widget(HelpScreen(name='help'))
    sm.add_widget(PromoScreen(name='promo'))
    sm.add_widget(FeedbackScreen(name='feedback'))

    # Парсеры
    sm.add_widget(AMDMParserScreen(name='amdm_parser'))
    sm.add_widget(MyTabsParserScreen(name='mytabs_parser'))
    sm.add_widget(AccordProParserScreen(name='accord_pro_parser'))
    sm.add_widget(AkkordusParserScreen(name='akkordus_parser'))
    sm.add_widget(MuzlandParserScreen(name='muzland_parser'))
    sm.add_widget(ChordieParserScreen(name='chordie_parser'))
    sm.add_widget(FiveLadParserScreen(name='fivelad_parser'))
    sm.add_widget(AkkordBardParserScreen(name='akkordbard_parser'))
    sm.add_widget(DomhveParserScreen(name='domhve_parser'))
    sm.add_widget(RushSoundParserScreen(name='rushsound_parser'))

    logger.info('ScreenManager настроен с NoTransition, добавлено 25 экранов')
    return sm