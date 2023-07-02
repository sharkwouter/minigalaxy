import datetime
from dataclasses import dataclass
from typing import List

import xml.etree.ElementTree as ET

from minigalaxy.entity.download_chunk import DownloadChunk
from minigalaxy.entity.xml_exception import XmlException


@dataclass
class DownloadInfo:
    name: str
    available: int
    not_availablemsg: str
    md5: str
    chunks: List[DownloadChunk]
    timestamp: datetime.datetime
    total_size: int

    @staticmethod
    def from_xml(xml: str) -> 'DownloadInfo':
        """
        Convert xml data into a DownloadInfo object
        Can throw XmlException if the xml is not readable
        :param xml: xml content as string
        :return: a new DownloadInfo object
        """
        try:
            xml_data = ET.fromstring(xml)
            if xml_data and xml_data.attrib:
                    download_data = DownloadInfo(
                        name=xml_data.attrib["name"],
                        available=int(xml_data.attrib.get("available", "0")),
                        not_availablemsg=xml_data.get("not_availablemsg", ""),
                        md5=xml_data.attrib["md5"],
                        chunks=[],
                        timestamp=datetime.datetime.fromisoformat(xml_data.attrib["timestamp"]),
                        total_size=int(xml_data.attrib["total_size"]),
                    )
                    for chunk in xml_data:
                        download_data.chunks.append(
                            DownloadChunk(
                                chunk_id=int(chunk.attrib["id"]),
                                from_byte=int(chunk.attrib["from"]),
                                to_byte=int(chunk.attrib["to"]),
                                method=chunk.attrib["method"],
                                checksum=chunk.text,
                            )
                        )
                    return download_data
        except (KeyError, ValueError, AssertionError, ET.ParseError) as e:
            raise XmlException(f"Could not process the following data as a download xml: {xml}") from e
        raise XmlException(f"Could not process the following data as a download xml: {xml}")
