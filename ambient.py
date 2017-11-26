"""plays an ambient mix with pygame. Mash CTRL+C to quit.
"""
__author__      = "Philooz"
__copyright__   = "2017 GPL"

import random, sys
import pygame, untangle

pygame.mixer.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

clock = pygame.time.Clock()

CLOCK_TICKER = 10

unit_duration_map = {
	'1m': 60*CLOCK_TICKER,
	'10m': 600*CLOCK_TICKER,
	'1h': 3600*CLOCK_TICKER
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
		self.play_at = None
		self.current_tick = 0
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

	def compute_next_ticks(self):
		val = unit_duration_map[self.random_unit]
		self.play_at = random.expovariate(self.random_counter/val)

	def play(self, force = False):
		if(not self.random and not self.mute):
			self.channel_object.play(self.sound_object, loops = -1)
		if(force):
			self.channel_object.play(self.sound_object)

	def tick(self):
		if(self.random and not self.mute):
			self.current_tick += 1
			if(self.play_at is None or self.current_tick > self.play_at):
				if(self.play_at is not None):
					self.play(True)
				self.current_tick = 0
				self.compute_next_ticks()
				#print("Recomputed : {}".format(self.play_at))

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

def bootstrap_chanlist(channels):
	for channel in channels:
		print('Loaded {}.'.format(channel))
		channel.play()
	print('Press CTRL+C to exit.')
	while True:
		clock.tick(CLOCK_TICKER)
		for channel in channels:
			channel.tick()

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description=__doc__)

	parser.add_argument('file',
			    help="XML file of the ambient mix to play. Make sure you have the correct \"sounds/\" folder in your current working directory.")

	args = parser.parse_args()

	bootstrap_chanlist(load_file(args.file))
