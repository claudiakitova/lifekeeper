"""Lifekeeper reads each format right: one small made-up file per format, then the page.

    python -m unittest discover -s tests
"""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "toolkit" / "lifekeeper"))
import lifekeeper  # noqa: E402


def meta(text):
    return text.encode("utf-8").decode("latin-1")


class Formats(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, text, encoding="utf-8"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding=encoding, newline="")  # line endings exactly as written, on every system
        return path

    def build(self, *me):
        return lifekeeper.build(self.root, list(me))

    def test_whatsapp_us_and_iphone_formats(self):
        self.write("WhatsApp Chat with Pat.txt", "7/4/19, 9:41 PM - Pat: Happy 4th!\n7/4/19, 9:45 PM - Me: You too!\n")
        self.write("WhatsApp Chat - Sam/_chat.txt", "[03.02.20, 18:22:10] Sam: hey\n[03.02.20, 18:23:01] Me: hi\n")
        life = self.build()
        self.assertEqual(life.people["Pat"]["first"], "2019-07-04")  # July 4, not April 7
        self.assertEqual(life.people["Sam"]["first"], "2020-02-03")
        self.assertEqual(life.people["Pat"]["mine"], 1)  # "Me" is in both chats, so it's me

    def test_telegram_owner_from_the_export(self):
        self.write("result.json", json.dumps({"personal_information": {"user_id": 1, "first_name": "Ana"}, "chats": {"list": [
            {"name": "Bo", "type": "personal_chat", "messages": [
                {"type": "message", "date": "2021-05-01T10:00:00", "from": "Ana", "from_id": "user1", "text": "hi"},
                {"type": "message", "date": "2021-05-02T10:00:00", "from": "Bo", "from_id": "user2", "text": "hey"}]}]}}))
        life = self.build()
        self.assertEqual(life.people["Bo"]["messages"], 2)
        self.assertEqual(life.sent["2021-05"], 1)

    def test_messenger_thread_with_meta_encoding(self):
        thread = {"participants": [{"name": meta("Zoë")}, {"name": meta("Ana")}], "messages": [
            {"sender_name": meta("Zoë"), "timestamp_ms": 1620000000000, "content": meta("café?")},
            {"sender_name": meta("Ana"), "timestamp_ms": 1620000100000, "content": "yes"}]}
        self.write("facebook/messages/inbox/zoe_1/message_1.json", json.dumps(thread))
        life = self.build("Ana")
        self.assertIn("Zoë", life.people)  # the broken encoding is fixed
        self.assertEqual(life.read["Messenger chats"], 1)

    def test_posts_and_retweets(self):
        self.write("your_posts_1.json", json.dumps([{"timestamp": 1600000000, "data": [{"post": meta("Привет")}]}]))
        self.write("data/tweets.js", "window.YTD.tweets.part0 = " + json.dumps([
            {"tweet": {"created_at": "Wed Oct 10 20:19:24 +0000 2018", "full_text": "my own words"}},
            {"tweet": {"created_at": "Wed Oct 10 21:19:24 +0000 2018", "full_text": "RT @someone: their words"}}]))
        life = self.build()
        texts = [text for items in life.posts.values() for _, _, text in items]
        self.assertIn("Привет", texts)
        self.assertIn("my own words", texts)
        self.assertNotIn("RT @someone: their words", texts)

    def test_calendar_with_folded_line_and_escapes(self):
        self.write("cal.ics", "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART;TZID=Europe/Berlin:20220401T090000\r\n"
                              "SUMMARY:Moving day\\, finally and a very long\r\n  title\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
        life = self.build()
        self.assertEqual(life.calendar["2022-04"], [("2022-04-01", "Moving day, finally and a very long title")])

    def test_spotify_both_formats(self):
        self.write("StreamingHistory_music_0.json", json.dumps([{"endTime": "2023-01-05 10:00", "artistName": "Björk", "msPlayed": 200000}]))
        self.write("Streaming_History_Audio_2023_0.json", json.dumps([
            {"ts": "2023-01-06T10:00:00Z", "master_metadata_album_artist_name": "Björk", "ms_played": 100000},
            {"ts": "2023-01-07T10:00:00Z", "master_metadata_album_artist_name": None, "ms_played": 100000}]))  # a podcast
        life = self.build()
        self.assertAlmostEqual(life.music["2023-01"]["Björk"], 5.0)

    def test_youtube_skips_ads(self):
        self.write("watch-history.json", json.dumps([
            {"header": "YouTube", "title": "Watched A talk", "subtitles": [{"name": "TED"}], "time": "2021-03-14T18:22:05.123Z"},
            {"header": "YouTube", "title": "Watched An ad", "subtitles": [{"name": "Brand"}], "time": "2021-03-14T18:00:00Z",
             "details": [{"name": "From Google Ads"}]}]))
        life = self.build()
        self.assertEqual(dict(life.watched["2021-03"]), {"TED": 1})

    def test_netflix_website_file(self):
        self.write("NetflixViewingHistory.csv", 'Title,Date\n"Dark: Season 1: Secrets","4/2/20"\n')
        life = self.build()
        self.assertEqual(dict(life.watched["2020-04"]), {"Dark": 1})

    def test_goodreads_skips_unread(self):
        self.write("goodreads_library_export.csv", "Title,Author,Date Read\nKitchen,Banana Yoshimoto,2025/04/16\nLater,Someone,\n")
        life = self.build()
        self.assertEqual(life.read["books read"], 1)

    def test_linkedin_positions(self):
        self.write("Positions.csv", "Company Name,Title,Started On,Finished On\nKran,Designer,Dec 2020,May 2024\n")
        life = self.build()
        self.assertEqual(life.work["2020-12"], [("2020-12", "Started as Designer at Kran")])
        self.assertEqual(life.work["2024-05"], [("2024-05", "Left Kran")])

    def test_keep_skips_trash(self):
        self.write("Keep/a.json", json.dumps({"title": "List", "textContent": "x", "createdTimestampUsec": 1600000000000000}))
        self.write("Keep/b.json", json.dumps({"title": "Gone", "isTrashed": True, "createdTimestampUsec": 1600000000000000}))
        life = self.build()
        self.assertEqual(life.read["Keep notes"], 1)

    def test_text_messages_hide_numbers(self):
        self.write("sms.xml", '<?xml version="1.0"?><smses count="2">'
                              '<sms address="+15550001111" date="1600000000000" type="1" body="hi" contact_name="Anna" />'
                              '<sms address="+15550002222" date="1600000100000" type="2" body="who?" contact_name="(Unknown)" /></smses>')
        life = self.build()
        self.assertIn("Anna", life.people)
        self.assertIn("an unknown number", life.people)
        self.assertNotIn("+15550002222", life.people)

    def test_mail_counts_only_what_i_sent(self):
        self.write("All mail.mbox", "From x Thu Jan 07 10:00:00 2021\nX-Gmail-Labels: Sent\nFrom: me@example.com\n"
                                    "To: Anna Berg <anna@example.com>\nDate: Thu, 07 Jan 2021 10:00:00 +0000\nSubject: hi\n\nhello\n\n"
                                    "From y Fri Jan 08 10:00:00 2021\nX-Gmail-Labels: Inbox\nFrom: news@example.com\n"
                                    "To: me@example.com\nDate: Fri, 08 Jan 2021 10:00:00 +0000\nSubject: sale\n\nbuy\n")
        life = self.build()
        self.assertEqual(list(life.people), ["Anna Berg"])

    def test_location_history_both_formats(self):
        self.write("Semantic Location History/2021/2021_AUGUST.json", json.dumps({"timelineObjects": [
            {"placeVisit": {"location": {"name": "Belém Tower"}, "duration": {"startTimestamp": "2021-08-14T10:12:00Z"}}}]}))
        self.write("Timeline.json", json.dumps({"semanticSegments": [
            {"startTime": "2025-04-06T10:00:00.000+09:00", "visit": {"topCandidate": {"placeLocation": {"latLng": "35.68°, 139.69°"}}}}]}))
        life = self.build()
        self.assertIn("Belém Tower", life.visits["2021-08"])
        self.assertIn("Tokyo", life.visits["2025-04"])

    def test_photos_in_a_zip_with_takeout_json(self):
        with zipfile.ZipFile(self.root / "takeout.zip", "w") as archive:
            archive.writestr("Takeout/Google Photos/IMG_1.jpg", b"not really a picture")
            archive.writestr("Takeout/Google Photos/IMG_1.jpg.json", json.dumps(
                {"photoTakenTime": {"timestamp": "1565000000"}, "geoData": {"latitude": 38.72, "longitude": -9.14}}))
            archive.writestr("Takeout/Google Photos/IMG_20190614_101500.jpg", b"no data, a date in the name")
        life = self.build()
        self.assertEqual(life.places["2019-08"]["Lisbon"], 1)
        self.assertEqual(life.photos["2019-06"], 1)

    def test_telegram_photo_names_and_impossible_dates(self):
        # Telegram Desktop names its photos with the day first; a camera with an unset clock writes "0000:00:00"
        self.write("DataExport/chats/chat_01/photos/photo_12@15-07-2023_12-02-58.jpg", b"not really a picture")
        life = self.build()
        self.assertEqual(life.photos["2023-07"], 1)
        self.assertIsNone(lifekeeper.real_day("0000-00-00"))
        self.assertIsNone(lifekeeper.real_day("2023-13-01"))
        self.assertEqual(lifekeeper.real_day("2023-07-15"), "2023-07-15")
        # a clock's starting day inside a photo isn't its date: the folder's year is used instead
        self.write("Stroidvor 2008/IMGA8299.jpg", b"not really a picture")
        self.write("Stroidvor 2008/IMGA8299.jpg.json", json.dumps({"photoTakenTime": {"timestamp": "946684800"}}))  # Jan 1, 2000
        life = self.build()
        self.assertEqual(life.photos_year["2008"], 1)
        self.assertEqual(life.photos["2000-01"], 0)

    def test_pictures_dated_by_their_exports(self):
        # Instagram and Facebook strip the dates from pictures but keep them in their JSON; X names a picture after its post
        self.write("instagram/media/posts/202101/111.jpg", b"not really a picture")
        self.write("instagram/your_instagram_activity/content/posts_1.json", json.dumps(
            [{"media": [{"uri": "media/posts/202101/111.jpg", "creation_timestamp": 1610000000, "title": ""}]}]))
        with zipfile.ZipFile(self.root / "twitter-archive.zip", "w") as archive:
            archive.writestr("data/tweets_media/1453000000000000000-AbC.jpg", b"a photo from a post")
            archive.writestr("assets/images/home-image.png", b"the archive viewer's own picture")
        self.write("DataExport/chats/chat_01/video_files/video_3@15-07-2023_12-02-58.mp4_thumb.jpg", b"a video's thumbnail")
        life = self.build()
        self.assertEqual(life.photos["2021-01"], 1)
        self.assertEqual(life.photos["2021-10"], 1)  # post 1453000000000000000 was written on Oct 26, 2021
        self.assertEqual(life.skipped["files in program, cache or hidden folders"], 1)
        self.assertEqual(life.skipped["video thumbnails"], 1)
        self.assertEqual(life.skipped["photos without a date"], 0)

    def test_searches_and_ai_chats(self):
        self.write("takeout/My Activity/Search/MyActivity.json", json.dumps([
            {"header": "Search", "title": "Searched for flights to lisbon", "time": "2021-08-01T10:00:00.000Z"},
            {"header": "Search", "title": "Searched for flights to lisbon", "time": "2021-08-02T10:00:00.000Z"},
            {"header": "Search", "title": "Visited Some page", "time": "2021-08-02T10:01:00.000Z"},
            {"header": "Search", "title": "Searched for an ad", "time": "2021-08-02T10:02:00.000Z", "details": [{"name": "From Google Ads"}]}]))
        self.write("chatgpt/conversations.json", json.dumps([
            {"title": "Packing list for Lisbon", "create_time": 1628500000.5, "mapping": {}},
            {"title": None, "create_time": 1628600000, "mapping": {}}]))
        life = self.build()
        self.assertEqual(dict(life.searches["2021-08"]), {"flights to lisbon": 2})
        self.assertEqual(life.asked["2021-08"], [("2021-08-09", "Packing list for Lisbon"), ("2021-08-10", "(no title)")])
        self.assertEqual((life.read["searches"], life.read["AI chats"]), (2, 2))
        page = lifekeeper.render(life, "x")
        self.assertIn("flights to lisbon", page)
        self.assertIn("Packing list for Lisbon", page)

    def test_stories_comments_and_cycles(self):
        self.write("instagram/your_instagram_activity/media/stories.json", json.dumps({"ig_stories": [
            {"uri": "media/stories/1.jpg", "creation_timestamp": 1615723200, "title": meta("Лиссабон!")},
            {"uri": "media/stories/2.jpg", "creation_timestamp": 1615726800, "title": ""}]}))
        self.write("instagram/your_instagram_activity/comments/post_comments_1.json", json.dumps([
            {"string_map_data": {"Comment": {"value": meta("Красота")}, "Media Owner": {"value": "anna.berg"}, "Time": {"timestamp": 1615730400}}}]))
        self.write("instagram/your_instagram_activity/comments/reels_comments.json", json.dumps({"comments_reels_comments": [
            {"string_map_data": {"Comment": {"value": "So good"}, "Media Owner": {"value": "leo"}, "Time": {"timestamp": 1615734000}}}]}))
        self.write("facebook/your_activity_across_facebook/comments_and_reactions/comments.json", json.dumps({"comments_v2": [
            {"timestamp": 1615737600, "data": [{"comment": {"comment": "Happy birthday!", "author": "Mira"}}], "title": "Mira commented"}]}))
        self.write("flo/flo.json", json.dumps({"operationalData": {"cycles": [
            {"period_start_date": "2021-03-02 00:00:00.0", "period_end_date": "2021-03-06 00:00:00.0"},
            {"period_start_date": "2021-03-30 00:00:00.0"}]}}))
        life = self.build()
        self.assertEqual(life.stories["2021-03"], [("2021-03-14", "Лиссабон!"), ("2021-03-14", "")])
        self.assertEqual(sorted(text for _, _, text in life.comments["2021-03"]), ["Happy birthday!", "So good", "Красота"])
        self.assertEqual(life.periods["2021-03"], ["2021-03-02", "2021-03-30"])
        self.assertEqual((life.read["Instagram stories"], life.read["comments I wrote"], life.read["periods (Flo)"]), (2, 3, 2))
        page = lifekeeper.render(life, "x")
        for text in ("stories (2)", "Лиссабон!", "Красота", "Mar 2, 2021, Mar 30, 2021"):
            self.assertIn(text, page)

    def test_time_tracker(self):
        self.write("timelogger.csv", "Activity type,Duration,From,To,Comment,Tags\n"
                                     "Work,08:30,\"Mar 1, 2021, 9:00 AM\",\"Mar 1, 2021, 5:30 PM\",,\n"
                                     "Work,07:00,2021-03-02 09:00,2021-03-02 16:00,,\n"
                                     "Reading,00:45,02.03.2021 20:00,02.03.2021 20:45,,\n"
                                     "Work,15:30,,,,\n")  # the totals at the end have no date
        life = self.build()
        self.assertEqual(round(life.hours["2021-03"]["Work"], 2), 15.5)
        self.assertEqual(round(life.hours["2021-03"]["Reading"], 2), 0.75)
        self.assertEqual(life.read["time tracker entries"], 3)
        self.assertIn("Work <span class=n>(16 h)</span>", lifekeeper.render(life, "x"))

    def test_mood_diaries(self):
        self.write("daylio_export.csv", "full_date,date,weekday,time,mood,activities,note_title,note\n"
                                        "2021-03-14,14 March,Sunday,21:00,rad,friends | party,,Met someone at the party.\n"
                                        "2021-03-15,15 March,Monday,21:00,good,work,,\n"
                                        "2021-03-16,16 March,Tuesday,21:00,good,work,,\n")
        self.write("beans/2022.csv", "date,mood,icons,short_diary,sleeps\n2022.12.30,4,\"walk, tea\",A quiet day.,\n2022.12.31,5,,,\n")
        life = self.build()
        self.assertEqual(life.diary["2021-03"], [("2021-03-14", "Met someone at the party.")])
        self.assertEqual(lifekeeper.mood_line(life.moods["2021-03"]), "mostly good <span class=n>(3 days)</span>")
        self.assertEqual(lifekeeper.mood_line(life.moods["2022-12"]), "4.5 on average <span class=n>(2 days)</span>")
        self.assertEqual(life.diary["2022-12"], [("2022-12-30", "A quiet day.")])
        self.assertEqual(life.read["mood diary days"], 5)

    def test_other_csv_files_are_left_alone(self):
        self.write("bank.csv", "date,amount,description\n2021-03-01,-12.50,coffee\n")
        life = self.build()
        self.assertFalse(life.moods or life.hours)

    def test_year_in_name(self):
        self.assertEqual(lifekeeper.year_in_name("Albums/1977/scan 3.jpg"), "1977")
        self.assertEqual(lifekeeper.year_in_name("1985 dacha.jpg"), "1985")
        self.assertIsNone(lifekeeper.year_in_name("IMG_1943.jpg"))  # a camera number
        self.assertIsNone(lifekeeper.year_in_name("e46141c79ac1903ee7b9f95a0915030d-360.jpg"))  # a hash holds no year
        self.assertIsNone(lifekeeper.year_in_name("photo1984x.jpg"))  # glued to letters: not a year on its own
        self.assertEqual(lifekeeper.year_in_name("archive_2007-2011/2008/November/Promo/Team/IMGA1.jpg"), "2008")  # deep, nearest year
        self.assertIsNone(lifekeeper.year_in_name("archive_2007-2011/misc/IMGA2.jpg"))  # a span of years isn't one year

    def test_sample_data_and_program_folders_are_left_out(self):
        # someone opens a whole downloaded copy of the project: the made-up demo and program folders stay out of their life
        self.write("project/demo/exports/.lifekeeper-sample", "made up\n")
        self.write("project/demo/exports/my_events.csv", "date,title,note\n2020-05-01,Mira's note,\n")
        self.write("project/node_modules/pkg/photo_1@01-01-2020_10-00-00.jpg", b"an icon")
        self.write("project/.cache/IMG_20200101_100000.jpg", b"a thumbnail")
        self.write("mine/my_events.csv", "date,title,note\n2021-06-01,My note,\n")
        life = self.build()
        self.assertEqual(list(life.notes), ["2021-06"])
        self.assertEqual(life.photos, {})
        self.assertEqual(life.skipped["files of the made-up sample data"], 1)
        self.assertEqual(life.skipped["files in program, cache or hidden folders"], 2)
        sample = lifekeeper.build(self.root / "project" / "demo" / "exports", [])  # opened on its own, it reads as usual
        self.assertEqual(list(sample.notes), ["2020-05"])

    def test_broken_file_is_counted_not_skipped_silently(self):
        self.write("broken.json", "{not json")
        self.write("my_events.csv", "date,title,note\n2020-12,First design job,\n")
        life = self.build()
        self.assertEqual(life.skipped["unreadable .json"], 1)
        self.assertEqual(life.notes["2020-12"][0][1], "First design job")

    def test_the_page(self):
        self.write("my_events.csv", "date,title,note\n2021-03-14,Met Leo,At a party\n")
        self.write("WhatsApp Chat with Leo.txt", "14.03.2021, 21:00 - Leo: hi\n14.03.2021, 21:01 - Me: hi!\n")
        page = lifekeeper.render(self.build("Me"), "Test")
        self.assertIn("Met Leo", page)
        self.assertIn("Mar 14, 2021", page)
        self.assertIn("Leo", page)
        self.assertNotIn("2021-03-14", page.split("<main>")[1])  # no machine dates on the page


class Places(unittest.TestCase):
    def test_names(self):
        self.assertEqual(lifekeeper.place_name(52.52, 13.40), "Berlin")
        self.assertEqual(lifekeeper.place_name(52.0, 13.9), "near Berlin")
        self.assertIsNone(lifekeeper.place_name(0, 0))  # 0,0 means "no location"
        self.assertTrue(lifekeeper.place_name(-60.0, -40.0).endswith("°"))


if __name__ == "__main__":
    unittest.main()
