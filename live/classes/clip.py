import logging

import live.query
import live.object
from live.constants import *
from live.query import Query

def make_getter(class_identifier, prop):
    def fn(self):
        return self.live.query("/live/%s/get/%s" % (class_identifier, prop), (self.track.index, self.index,))[2]

    return fn

def make_setter(class_identifier, prop):
    def fn(self, value):
        self.live.cmd("/live/%s/set/%s" % (class_identifier, prop), (self.track.index, self.index, value))

    return fn
from dataclasses import dataclass

@dataclass
class ClipDetails:
    name: str
    length: int
    signature_numerator: int
    signature_denominator: int
    start_marker: float
    end_marker: float
    loop_start: float
    loop_end: float

class Clip:
    """
    An object representing a single clip in a Live set.
    """

    def __init__(self, track, index: int, name: str, length: float = 4):
        """ Create a new clip.

        Args:
            track: A Track or Group object
            index: The index of this clip within the track
            name: The human-readable name of the clip
            length: Length of the clip, in beats
        """
        self.track = track
        self.set = self.track.set
        self.index = index
        self.name = name
        self.length = length
        self.state = CLIP_STATUS_STOPPED
        self.logger = logging.getLogger(__name__)
        # self.live = Query()

    @property
    def live(self):
        return Query()

    def __str__(self):
        name = ": %s" % self.name if self.name else ""
        state_symbols = {
            CLIP_STATUS_EMPTY: " ",
            CLIP_STATUS_STOPPED: "-",
            CLIP_STATUS_PLAYING: ">",
            CLIP_STATUS_STARTING: "*"
        }
        state_symbol = state_symbols[self.state]

        return "Clip (%d,%d)%s [%s]" % (self.track.index, self.index, name, state_symbol)

    def __getstate__(self):
        return {
            "track": self.track,
            "index": self.index,
            "name": self.name,
            "length": self.length,
        }

    def __setstate__(self, d: dict):
        self.track = d["track"]
        self.index = d["index"]
        self.name = d["name"]
        self.length = d["length"]

    def play(self):
        """
        Start playing clip.
        Must use clip_slot (not clip) as this is also used in group tracks, which have clip_slots without clips.
        """
        self.live.cmd("/live/clip_slot/fire", (self.track.index, self.index))
        self.track.playing = True
        if type(self.track) is live.Group:
            for track in self.track.tracks:
                #------------------------------------------------------------------------
                # when we trigger a group clip, it triggers each of the corresponding
                # clips in the tracks it contains. thus need to update the playing
                # status of each of our tracks, assuming that all clips/stop buttons
                # are enabled.
                #------------------------------------------------------------------------
                if self.index < len(track.clips) and track.clips[self.index] is not None:
                    track.playing = True
                else:
                    track.playing = False

    def stop(self):
        """
        Stop playing clip.
        """
        self.live.cmd("/live/clip/stop", (self.track.index, self.index))
        self.track.playing = False

    @property
    def details(self) -> ClipDetails:
        """
        Return details of the clip.
        """
        details_tuple = self.live.query("/live/clip/get/details", (self.track.index, self.index))
        return ClipDetails(*details_tuple[2:])

    @property
    def notes(self) -> list[tuple[int, float, float, int, bool]]:
        """
        Return all notes in the clip.
        """
        response: list[int] = self.live.query("/live/clip/get/notes", (self.track.index, self.index))
        # first two values in response are track and clip index
        # the rest are notes in the form of: (pitch, start_time, duration, velocity, mute)
        # but we want to return them as tuples
        # so we slice the response into chunks of 5 and return them as tuples
        return [tuple(response[2:][i:i + 5]) for i in range(0, len(response[2:]), 5)]

    def remove_notes(self) -> None:
        """
        Clear all notes in the clip.
        """        
        self.live.cmd("/live/clip/remove/notes", (self.track.index, self.index))

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
        self.live.cmd("/live/clip/add/notes", (self.track.index, self.index, pitch, start_time, duration, velocity, mute))

    def set_name(self, name: str) -> None:
        """
        Set the name of the clip.
        """
        self.live.cmd("/live/clip/set/name", (self.track.index, self.index, name))

    signature_numerator = property(fget=make_getter("clip", "signature_numerator"),
                                   fset=make_setter("clip", "signature_numerator"),
                                   doc="Time signature numerator")

    signature_denominator = property(fget=make_getter("clip", "signature_denominator"),
                                     fset=make_setter("clip", "signature_denominator"),
                                     doc="Time signature denominator")

    start_marker = property(fget=make_getter("clip", "start_marker"),
                            fset=make_setter("clip", "start_marker"),
                            doc="Start marker in beats")

    end_marker = property(fget=make_getter("clip", "end_marker"),
                          fset=make_setter("clip", "end_marker"),
                          doc="End marker in beats")

    loop_start = property(fget=make_getter("clip", "loop_start"),
                          fset=make_setter("clip", "loop_start"),
                          doc="Loop start time in beats")

    loop_end = property(fget=make_getter("clip", "loop_end"),
                        fset=make_setter("clip", "loop_end"),
                        doc="Loop end time in beats")

    pitch_coarse = property(fget=make_getter("clip", "pitch_coarse"),
                            fset=make_setter("clip", "pitch_coarse"),
                            doc="Coarse pitch bend")

    is_playing = property(fget=make_getter("clip", "is_playing"),
                          fset=make_setter("clip", "is_playing"),
                          doc="True if the clip is playing, False otherwise")

    is_midi_clip = property(fget=make_getter("clip", "is_midi_clip"),
                            fset=make_setter("clip", "is_midi_clip"),
                            doc="True if the clip is a MIDI clip, False otherwise")

    is_audio_clip = property(fget=make_getter("clip", "is_audio_clip"),
                             fset=make_setter("clip", "is_audio_clip"),
                             doc="True if the clip is an audio clip, False otherwise")
