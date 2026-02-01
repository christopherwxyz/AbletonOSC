"""Browser handler for loading devices and presets."""

from typing import Tuple, Any
from .handler import AbletonOSCHandler


class BrowserHandler(AbletonOSCHandler):
    """Handler for browser operations like loading instruments and effects."""

    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    def init_api(self):
        """Initialize browser API endpoints."""
        self.osc_server.add_handler("/live/browser/load_instrument",
                                    self._load_instrument)
        self.osc_server.add_handler("/live/browser/load_drum_kit",
                                    self._load_drum_kit)
        self.osc_server.add_handler("/live/browser/load_default_instrument",
                                    self._load_default_instrument)

    @property
    def browser(self):
        """Get the application browser."""
        return self.manager.application.browser

    def _find_item_by_name(self, parent, name: str):
        """Recursively find a browser item by name."""
        for item in parent.children:
            if item.name.lower() == name.lower():
                return item
            # Search in children
            if item.children:
                found = self._find_item_by_name(item, name)
                if found:
                    return found
        return None

    def _get_first_loadable_child(self, item):
        """Get the first loadable item from a browser item's children."""
        if item.is_loadable:
            return item
        for child in item.children:
            if child.is_loadable:
                return child
            found = self._get_first_loadable_child(child)
            if found:
                return found
        return None

    def _load_instrument(self, params: Tuple[Any]):
        """
        Load an instrument by name onto the selected track.

        Usage: /live/browser/load_instrument <instrument_name>
        Example: /live/browser/load_instrument "Simpler"
        """
        if len(params) < 1:
            self.logger.error("load_instrument requires instrument name")
            return

        name = str(params[0])
        self.logger.info(f"Loading instrument: {name}")

        try:
            # Navigate to Instruments in the browser
            browser = self.browser
            instruments = None

            # Find Instruments folder
            for item in browser.instruments.children:
                if name.lower() in item.name.lower():
                    instruments = item
                    break

            if not instruments:
                # Try searching in all instruments
                instruments = self._find_item_by_name(browser.instruments, name)

            if instruments:
                # Get a loadable item
                loadable = self._get_first_loadable_child(instruments)
                if loadable:
                    browser.load_item(loadable)
                    self.logger.info(f"Loaded: {loadable.name}")
                    return (loadable.name,)
                else:
                    self.logger.warning(f"No loadable item found for: {name}")
            else:
                self.logger.warning(f"Instrument not found: {name}")

        except Exception as e:
            self.logger.error(f"Error loading instrument: {e}")

    def _load_drum_kit(self, params: Tuple[Any]):
        """
        Load a drum kit onto the selected track.

        Usage: /live/browser/load_drum_kit [kit_name]
        Example: /live/browser/load_drum_kit "808"
        """
        try:
            browser = self.browser
            drums = browser.drums

            if len(params) > 0:
                name = str(params[0])
                item = self._find_item_by_name(drums, name)
            else:
                # Load first available drum kit
                item = self._get_first_loadable_child(drums)

            if item and item.is_loadable:
                browser.load_item(item)
                self.logger.info(f"Loaded drum kit: {item.name}")
                return (item.name,)
            else:
                self.logger.warning("No drum kit found")

        except Exception as e:
            self.logger.error(f"Error loading drum kit: {e}")

    def _load_default_instrument(self, params: Tuple[Any]):
        """
        Load a default instrument onto the selected track.
        Prefers synthesizers (Drift, Analog, Wavetable) over samplers (Simpler)
        because synths produce sound immediately without needing samples.

        Usage: /live/browser/load_default_instrument
        """
        try:
            browser = self.browser

            # Prefer synths over samplers - synths make sound without samples
            # Simpler/Sampler are samplers that need samples to make sound
            for name in ["Drift", "Analog", "Wavetable", "Operator", "Tension", "Collision"]:
                item = self._find_item_by_name(browser.instruments, name)
                if item:
                    loadable = self._get_first_loadable_child(item)
                    if loadable:
                        browser.load_item(loadable)
                        self.logger.info(f"Loaded default instrument: {loadable.name}")
                        return (loadable.name,)

            # Fallback: try to load any instrument
            loadable = self._get_first_loadable_child(browser.instruments)
            if loadable:
                browser.load_item(loadable)
                self.logger.info(f"Loaded instrument: {loadable.name}")
                return (loadable.name,)

            self.logger.warning("No default instrument found")

        except Exception as e:
            self.logger.error(f"Error loading default instrument: {e}")
