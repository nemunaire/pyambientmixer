"""plays an ambient mix with pygame. Mash CTRL+C to quit.
"""
__author__      = "Philooz"
__copyright__   = "2017 GPL"

import asyncio
import random, sys
import pygame, untangle

loop = asyncio.get_event_loop()
pygame.mixer.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)

unit_duration_map = {
	'1m': 60,
	'10m': 600,
	'1h': 3600
}

class Channel():
	def __init__(self, channel_id, sound_id, name = "", volume = 100, random = False, random_counter = 1, random_unit = "1h", mute = False, balance = 0):
		try:
			self.sound_object = pygame.mixer.Sound("sounds/{}.ogg".format(sound_id))
		except:
			print('Error while loading sound "sounds/{}.ogg". Did you convert it to ogg?'.format(sound_id))
			sys.exit()
		self.channel_object = pygame.mixer.Channel(channel_id)
		self.name = name
		#Normalize volume
		self.volume = volume
		self.sound_object.set_volume(int(volume)/100.0)
		#Adjust balance
		self.balance = balance
		self.left_volume = 1.0 if (balance <= 0) else (1.0-float(balance)/100)
		self.right_volume = 1.0 if (balance >= 0) else (1.0+float(balance)/100)
		self.channel_object.set_volume(self.left_volume, self.right_volume)
		#Set random
		self.channel_id = channel_id
		self.sound_id = sound_id
		self.random = random
		self.random_counter = random_counter
		self.random_unit = random_unit
		self.mute = mute

	def __repr__(self):
		if(self.random):
			return "Channel {channel_id} : {name} (random {ran} per {unit}), {sound_id}.ogg (volume {vol}, balance {bal})".format(
			channel_id=self.channel_id,
			name=self.name,
			sound_id=self.sound_id,
			vol=self.volume,
			bal=self.balance,
			ran=self.random_counter,
			unit=self.random_unit)
		else:
			return "Channel {channel_id} : {name} (looping), {sound_id}.ogg (volume {vol}, balance {bal})".format(
			channel_id=self.channel_id,
			name=self.name,
			sound_id=self.sound_id,
			vol=self.volume,
			bal=self.balance)

	@property
	def next_tick(self):
		return random.expovariate(self.random_counter/unit_duration_map[self.random_unit])

	def play_once(self):
		self.channel_object.play(self.sound_object)

	def play_loop(self):
		self.channel_object.play(self.sound_object, loops=-1)

def load_file(xml_file):
	obj = untangle.parse(xml_file)
	channels = []
	for channel in obj.audio_template.get_elements():
		if channel._name[:7] == "channel" and channel.id_audio.cdata not in ("", "0"):
			channel_id = int(channel._name[7:]) - 1
			channels.append(
				Channel(
					channel_id,
					channel.id_audio.cdata,
					name=channel.name_audio.cdata,
					volume=channel.volume.cdata,
					random=channel.random.cdata == "true",
					random_counter=int(channel.random_counter.cdata),
					random_unit=channel.random_unit.cdata,
					mute=channel.mute.cdata == "true",
					balance=int(channel.balance.cdata),
				)
			)
	return channels

def run(channels):
	for channel in channels:
		print('Loaded {}.'.format(channel))
		if not channel.random and not channel.mute:
			channel.play_loop()
		else:
			def play(channel):
                                loop.call_later(channel.next_tick, play, channel)
                                channel.play_once()
			loop.call_later(channel.next_tick, play, channel)

	print('Press CTRL+C to exit.')

	try:
		loop.run_forever()
	finally:
		loop.close()

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)

	parser.add_argument('file',
			    help="XML file of the ambient mix to play. Make sure you have the correct \"sounds/\" folder in your current working directory.")

	args = parser.parse_args()

	run(load_file(args.file))
