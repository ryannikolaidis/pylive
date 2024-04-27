import logging

import live.query
import live.object
from live.constants import *
from live.query import Query
from .clip import ClipDetails

class DetailClip():
    """
    A class representing a single detail clip in a Live set.
    """

    @classmethod
    def fetch_details(self) -> ClipDetails:
        """
        Return details about the clip.
        """
        details_tuple = Query().query("/live/view/detail_clip/get/details")
        return ClipDetails(*details_tuple)

    @classmethod
    def get_notes(self) -> list[tuple[int, float, float, int, bool]]:
        """
        Return all notes in the clip.
        """
        response: list[int] = Query().query("/live/view/detail_clip/get/notes")
        # first two values in response are track and clip index
        # the rest are notes in the form of: (pitch, start_time, duration, velocity, mute)
        # but we want to return them as tuples
        # so we slice the response into chunks of 5 and return them as tuples
        return [tuple(response[i:i + 5]) for i in range(0, len(response), 5)]

    @classmethod
    def remove_notes(self) -> None:
        """
        Clear all notes in the clip.
        """        
        Query().cmd("/live/view/detail_clip/remove/notes")

    @classmethod
    def add_note(self,
                 pitch: int,
                 start_time: float,
                 duration: float,
                 velocity: int,
                 mute: bool) -> None:
        """
        Add a MIDI note event to this clip.

        Args:
            pitch: The MIDI pitch of the note, where 60 = C3
            start_time: The floating-point start time in the clip, in beats
            duration: The floating-point duration of the note, in beats
            velocity: The MIDI velocity of the note, from 0..127
            mute: If True, mutes the note.
        """
        Query().cmd("/live/view/detail_clip/add/notes", (pitch, start_time, duration, velocity, mute))
