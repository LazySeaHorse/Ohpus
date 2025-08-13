"""Tag handling and metadata preservation."""

import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO

from mutagen import FileType, File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, PictureType
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
from PIL import Image


logger = logging.getLogger(__name__)


class TagHandler:
    """Handle metadata transfer between formats."""
    
    # ID3 to Vorbis comment mapping
    TAG_MAPPING = {
        'TIT2': 'TITLE',
        'TPE1': 'ARTIST',
        'TPE2': 'ALBUMARTIST', 
        'TALB': 'ALBUM',
        'TDRC': 'DATE',
        'TYER': 'DATE',
        'TCON': 'GENRE',
        'TRCK': 'TRACKNUMBER',
        'TPOS': 'DISCNUMBER',
        'TPE3': 'CONDUCTOR',
        'TPE4': 'REMIXER',
        'TCOM': 'COMPOSER',
        'TEXT': 'LYRICIST',
        'TIT1': 'GROUPING',
        'TIT3': 'SUBTITLE',
        'TPUB': 'PUBLISHER',
        'TCOP': 'COPYRIGHT',
        'TENC': 'ENCODEDBY',
        'TBPM': 'BPM',
        'TMOO': 'MOOD',
        'TSRC': 'ISRC',
        'COMM': 'COMMENT',
    }
    
    @classmethod
    def copy_tags(cls, source_path: Path, dest_path: Path) -> bool:
        """
        Copy tags from source to destination file.
        
        Args:
            source_path: Source audio file
            dest_path: Destination Opus file
        
        Returns:
            True if successful
        """
        try:
            # Load source file
            source = File(str(source_path))
            if not source:
                logger.warning(f"Could not read source file: {source_path}")
                return False
            
            # Load destination file
            dest = OggOpus(str(dest_path))
            
            # Copy standard tags
            if isinstance(source, MP3):
                cls._copy_id3_to_vorbis(source, dest)
            else:
                cls._copy_generic_tags(source, dest)
            
            # Copy album art
            cls._copy_album_art(source, dest)
            
            # Save destination
            dest.save()
            logger.debug(f"Tags copied successfully to {dest_path}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to copy tags: {e}")
            return False
    
    @classmethod
    def _copy_id3_to_vorbis(cls, source: MP3, dest: OggOpus):
        """Copy ID3 tags to Vorbis comments."""
        if not source.tags:
            return
        
        for id3_key, vorbis_key in cls.TAG_MAPPING.items():
            if id3_key in source.tags:
                value = source.tags[id3_key]
                
                # Handle different value types
                if hasattr(value, 'text'):
                    # Multi-value support
                    if len(value.text) > 1:
                        dest[vorbis_key] = [str(t) for t in value.text]
                    elif len(value.text) == 1:
                        dest[vorbis_key] = str(value.text[0])
                else:
                    dest[vorbis_key] = str(value)
        
        # Handle track/disc numbers with totals (e.g., "3/12")
        cls._parse_track_disc_numbers(source, dest)
    
    @classmethod
    def _copy_generic_tags(cls, source: FileType, dest: OggOpus):
        """Copy tags from generic source."""
        if not source.tags:
            return
        
        # Direct copy for formats with similar tag structure
        for key, value in source.tags.items():
            if isinstance(value, list):
                dest[key.upper()] = value
            else:
                dest[key.upper()] = str(value)
    
    @classmethod
    def _parse_track_disc_numbers(cls, source: MP3, dest: OggOpus):
        """Parse track/disc numbers with totals."""
        # Track number
        if 'TRCK' in source.tags:
            track = str(source.tags['TRCK'].text[0])
            if '/' in track:
                num, total = track.split('/', 1)
                dest['TRACKNUMBER'] = num
                dest['TRACKTOTAL'] = total
            else:
                dest['TRACKNUMBER'] = track
        
        # Disc number
        if 'TPOS' in source.tags:
            disc = str(source.tags['TPOS'].text[0])
            if '/' in disc:
                num, total = disc.split('/', 1)
                dest['DISCNUMBER'] = num
                dest['DISCTOTAL'] = total
            else:
                dest['DISCNUMBER'] = disc
    
    @classmethod
    def _copy_album_art(cls, source: FileType, dest: OggOpus):
        """Copy album art to Opus file."""
        try:
            picture_data = cls._extract_album_art(source)
            if picture_data:
                cls._embed_album_art(dest, picture_data)
        except Exception as e:
            logger.warning(f"Failed to copy album art: {e}")
    
    @classmethod
    def _extract_album_art(cls, source: FileType) -> Optional[Dict[str, Any]]:
        """Extract album art from source file."""
        if isinstance(source, MP3) and source.tags:
            # Look for APIC frames
            for key in source.tags:
                if key.startswith('APIC'):
                    apic = source.tags[key]
                    # Prefer front cover
                    if apic.type == PictureType.COVER_FRONT or not hasattr(cls, '_found_cover'):
                        cls._found_cover = True
                        return {
                            'data': apic.data,
                            'mime': apic.mime,
                            'type': apic.type,
                            'desc': apic.desc
                        }
        
        # Handle other formats with Picture blocks
        if hasattr(source, 'pictures') and source.pictures:
            pic = source.pictures[0]
            return {
                'data': pic.data,
                'mime': pic.mime,
                'type': pic.type,
                'desc': pic.desc
            }
        
        return None
    
    @classmethod
    def _embed_album_art(cls, dest: OggOpus, picture_data: Dict[str, Any]):
        """Embed album art into Opus file using METADATA_BLOCK_PICTURE."""
        pic = Picture()
        pic.data = picture_data['data']
        pic.mime = picture_data['mime']
        pic.type = picture_data.get('type', PictureType.COVER_FRONT)
        pic.desc = picture_data.get('desc', '')
        
        # Get image dimensions
        try:
            img = Image.open(BytesIO(pic.data))
            pic.width, pic.height = img.size
            pic.depth = {"RGB": 24, "RGBA": 32}.get(img.mode, 24)
        except:
            pic.width = pic.height = 0
            pic.depth = 24
        
        # Encode to base64
        pic_data = pic.write()
        pic_base64 = base64.b64encode(pic_data).decode('ascii')
        
        # Add to Opus file
        dest['METADATA_BLOCK_PICTURE'] = [pic_base64]
    
    @classmethod
    def add_encoder_tag(cls, opus_path: Path, encoder_info: str):
        """Add encoder information tag."""
        try:
            opus = OggOpus(str(opus_path))
            opus['ENCODER'] = encoder_info
            opus['ENCODED_BY'] = 'Oh OPUS'
            opus.save()
        except Exception as e:
            logger.warning(f"Failed to add encoder tag: {e}")