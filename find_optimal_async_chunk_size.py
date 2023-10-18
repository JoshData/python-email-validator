# Try different chunk sizes to find the optimal
# size for the fastest performance.
#
# Read in a list of email addresses on STDIN and
# draw from it random addresses for each call.

import asyncio
import random
import sys
import time

from email_validator import validate_email_async, EmailNotValidError, \
  caching_async_resolver

async def wrap_validate_email(email, dns_resolver):
  # Wrap validate_email_async to catch
  # exceptions.
  try:
    return await validate_email_async(email, dns_resolver=dns_resolver)
  except EmailNotValidError as e:
    return e

async def is_valid(email, dns_resolver):
  try:
    await validate_email_async(email, dns_resolver=dns_resolver)
    return True
  except EmailNotValidError as e:
    return False

async def go():
  # Read in all of the test addresses from STDIN.
  all_email_addreses = [line.strip() for line in sys.stdin.readlines()]

  # Sample the whole set and throw out addresses that are
  # invalid.
  resolver = caching_async_resolver(timeout=5)
  all_email_addreses = random.sample(all_email_addreses, 10000)
  all_email_addreses = [email for email in all_email_addreses
    if is_valid(is_valid, resolver)]

  print("Starting...")

  # Start testing various chunk sizes.
  for chunk_size in range(1, 200):
    reps = max(1, int(15 / chunk_size))

    # Draw a random sample of email addresses to use
    # in this test. For low chunk sizes where we perform
    # multiple reps, draw the samples for all of the
    # reps ahead of time so that we don't time the
    # sampling.
    samples = [
      random.sample(all_email_addreses, chunk_size)
      for _ in range(reps)
    ]

    # Create a resolver with a short timeout.
    # Use a caching resolver to better reflect real-world practice.
    resolver = caching_async_resolver(timeout=5)
    resolver.nameservers = ["8.8.8.8"]

    # Start timing.
    t_start = time.time_ns()

    # Run the reps.
    for i in range(reps):
      # Run the chunk.
      coros = [
        wrap_validate_email(email, dns_resolver=resolver)
        for email in samples[i]]
      await asyncio.gather(*coros)

    # End timing.
    t_end = time.time_ns()

    duration = t_end - t_start

    print(chunk_size, int(round(duration / (chunk_size * reps) / 1000)), sep='\t')

asyncio.run(go())
