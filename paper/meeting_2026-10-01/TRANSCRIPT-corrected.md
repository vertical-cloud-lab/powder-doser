# Corrected transcript: 1 October 2026 meeting (Sam Charles, Sterling Baird)

The meeting ran for 55 minutes, starting at 13:16:56 MDT (19:16:56 UTC). The source is
the raw Tactiq export,
[`Powder Doser Manuscript Overview.txt`](../../Powder%20Doser%20Manuscript%20Overview.txt).
The summary is in [MEETING-NOTES.md](MEETING-NOTES.md), and the questions that came out
of it are in [MEETING-DECISIONS.md](MEETING-DECISIONS.md).

**How this was edited.** This follows the 11 May transcript's method: a cleaned,
line-by-line edit of the voice-to-text output.
- Tactiq repeats most passages two or three times; each is given once here.
- Obvious mishearings are corrected (glossary at the end). Quoted words are kept
  wherever the meaning was clear. Words in [brackets] are added for sense.
- "[?]" marks a word or phrase that could not be recovered.
- Personal conversation, a phone call, and screen-sharing and audio logistics are left
  out, each replaced by a one-line note.
- No credentials were spoken or shown in the transcript. The recording was paused while
  the API key was created.

**Speakers.** Tactiq credits everything up to 10:25 to Sterling and everything from 11:17
to Sam, but both spoke throughout. The labels below are inferred from context: what each
person knew, asked for or did on GitHub at that moment. A label with "?" is a guess, and
"—" means the speaker is unclear. Speaker labels should be checked against the video.

---

## Part 1: Sam's points on the manuscript (00:00–10:25)

**00:00 Sam:** Most of it [is] small things, like accuracy. Some of it is kind of
surprising; at a couple of points it says something that just isn't true. Usually we'd
just look at this ourselves, but there are a couple of things I wanted to raise with
you, and that's mostly what I wanted to get out of this. After that, if you want, we can
walk through it.
**—:** Has the meeting [recording] started? — Yeah. Perfect.

**00:48 Sam:** So, tilt range. The test that we ran, the 13 powder tests: I think they
went all the way to vertical. It just says [0–45°]. This is a question; I should know
this.

**01:48 Sterling:** Let me see. I remember that it's in the results we got. [Was it]
really 90°? So I'll send this off. *[Sterling posts the "max 2 sentences" request on #97
at 19:19 UTC, asking Claude to check the livestreams.]* For something like this, where
it's really more of a side tangent, I've found it useful to say "max two sentences".
Otherwise it's going to write a crazy run-on sentence. It has at least trimmed it down.
I should have reduced the reasoning. It really does speed things up if you use Opus with
medium effort. There's low, medium, high, extra high and then max. Max is what I have set
as the default for all the repositories, partly because of the asynchronous nature of
it: you send a ping, and you want it to do a good job on its own before it gets back.
But it certainly takes its time. *[Aside about a stray @claude ping with no
instruction, which Claude answered briefly. Omitted.]*

**04:00:** *[Aside about using AI more generally, for example ChatGPT for career
research. Omitted.]*

**04:00 Sam:** OK. Not all of these things needed to be brought up with you. This is one
of the things that was wrong.

**04:40 Sam:** It says it's filled through these loading slots in the top.
**Sterling?:** Yeah, I remember that.
**—:** You've gotten rid of that, like, months ago.
**Sam:** And it's just that we're using supports in the printing; we totally use
supports. I want to look at these figures in a second; we have to adjust them a little
bit. But in the abstract, it just says…

**05:14 Sam:** "smaller doses less reliable", and it doesn't say that we're going to fix
that, and we've been doing stuff on that that's great. I'd just add a little bit, like
"we're doing controls research to figure out [small doses]".

**05:30 Sam:** The design log we have just needs to be refreshed, basically with the
updates. And a couple of times it said that late in the project we introduced Zoo. I
think that's unnecessary. And it said that later versions can arrange several channels
around one cup, and that's not necessarily the way we're going to do it. And it brought
up these different "generations": the first generation was the powder-excavator idea,
then they picked the auger and went through that. I was like, it's been us the whole
time. This is less than a year of work. I don't know what you're talking about.

**06:10 Sterling?:** Months, right?
**Sam:** Yeah. We're not talking about the next team coming on after I graduated.
**Sterling?:** So, technically, there were two people that I worked with during this
one- or two-day hackathon.
**Sam:** Yeah, right, exactly.
**Sterling?:** But that was the "first generation" of things. That's funny.
**Sam:** So I don't know what word to use there. I tried sprints, or research thrusts, or
something like that.
**—:** Phases might be a good word. Or just different terminology: versions.

**06:46 Sam:** Maybe it said that already. I don't know why it said that. I needed to
bring all of these up with you. There was a list of things where I specifically said,
"make a note that we should talk about that." The rest are just small things.

**07:15 Sterling:** Is it still running? Yes, it's still running. I just noticed there
wasn't a PDF link yet. Normally, if it was done, I'd expect "here's the new PDF with all
the fixes." So, good. And yes, it's been sent on the tilt angle.

**07:54 Sam:** Is this transcription going to [go to] Claude as well?
**Sterling:** Not immediately, but the idea was that we take this and put it in there.
**Sam:** So if I say something right now, I don't have to write it down.
**Sterling:** Exactly.

**08:14 Sam?:** There's some reference to Will's work: now it's just a control problem,
so we're working on that. And on top of that, adding the fact that we've actually used
it with [the] atomizer [?]. I think that's good; it's quite broad. That's one of the
recent updates. I was going to mention the new auger in the comments. Actually, I want
to talk about this.

**09:03 Sam:** [The] figure: it doesn't know that we made this new auger, which has the
reservoir for two-thirds [of its length]. It says the screw runs throughout; it's not
like that. I might also have changed some things about the screw, so make sure the data
in here is still accurate.
**Sterling?:** Part of this gets into the idea of: where are the reproducible build
instructions for this thing?

**09:39 Sterling?:** If we have those, and we just point Claude to the build
instructions, then it could probably grab [the right files].
**Sam?:** That's true, if you're doing it like a tutorial.
**Sterling?:** Or let's just throw the video at it. Because that's the kind of thing
that says "here's the file that you print", and now we've got all those other ones.

**10:09:** *[Aside: a scene from *The Italian Job*. Omitted.]*

**10:25 —:** OK, so this is the first figure. The big figure should explain what we're
doing. A couple of thoughts on this. You mentioned screen sharing for this.
*[Audio and screen-sharing logistics omitted.]*

## Part 2: Fig. 1 (11:17–13:31)

**11:17 Sam:** OK, so this is the figure, and [most of it] is great. I like all the ideas
we have here.

**12:01 Sam:** Starting at panel A: this is a little out of date. You can see that B is
the actual updated picture, and it has our human-made parts. A lot of [A] is just
stand-ins. The stepper motor is a stand-in for the actual stepper, there's no solenoid
on it, and the tap collar has been updated anyway. So it might be good to get an
updated picture.
**Sterling:** Do we have a render?
**Sam:** We don't have a current render. I don't even know if we have a current
assembly. So that's where we're at.

**12:55 —:** So either we can make it, which is a great thing we could have somebody in
the lab do. We have Brandon and Ethan helping out now, so that might be a great job for
them. Or it could just be a nice picture of it that we take.
**Sam:** But it should be updated. I love the idea of it, but it should be updated.

## Part 3: Getting the CAD to Claude (13:31–24:47)

**13:31 Sam?:** And I think some of the files are on Fusion still.
**Sterling?:** Maybe all the files?
**Sam?:** No, not all the files.
*[Sterling posts on #165 at 19:31 UTC: "We need a new assembly and then a new render ...
Some files are still on Fusion, some on OnShape."]*
**Sterling:** Can I have you do something? Could you log on to Onshape?

**14:21:** *[Recording and screen sharing paused while credentials were on screen.]*

**15:12 Sterling:** Go to the Vertical Cloud Lab classroom settings, then Developer. Or
actually, go back over to My Account, then Developer, then API keys. You can name it
something like "powder-doser". [Scopes:] read profile information, read documents,
write, share and unshare. Create it, and copy both keys into a notepad for now.

**16:06 Sterling:** Then go to the powder-doser repository, Settings, then "Secrets and
variables", then Actions, then "New repository secret". Name it `ONSHAPE_ACCESS_KEY`, in
all caps with underscores, and paste the access key. Then do the same for the secret
key.

**17:50:** *[Sterling took a phone call. The personal conversation that followed is
omitted.]*

**19:29 Sam:** Am I replacing that one, or is it specific to me?
**Sterling:** That one's for Copilot. I was actually surprised: it looks like I just
never updated it so that Claude could use Onshape, because we were still using Copilot
at the time.

**20:10 Sterling:** I'm having you add your account because the BYU VCL one has that
2,500 quota. My thought is that if people in the lab use their own developer API keys,
we probably won't run into the API limit. If we run yours to the max, we'll just use
somebody else's.

**20:30 Sterling:** Now go to Code, then `.github/workflows/claude.yml`. Click the edit
button, the little pencil. Scroll down to all the secrets. Maybe put it after the
McMaster one; it doesn't really matter. You'll follow the same pattern:
`ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY`. Then "Commit changes" at the top. Notice
that you're committing to the main branch. Go ahead and click that.
*[Sam's commit `52ec03a`, "Update claude.yml", lands on `main` at 19:40 UTC.]*

**23:11 Sterling:** Committing it to the main branch was important, because Claude only
looks at this YAML file on the main branch. It doesn't matter what you're doing in any
other branch; Claude is only triggered by, and only respects, what's written here. This
file controls everything about how Claude runs. The whole "@claude+opus" thing is parsed
here: it's a very long file, and this is all pattern-matching for the plus, the colon
and so on.
**Sam:** Is this where the Copilot instructions [equivalent] lives, where we tell it
what to do in general?
**Sterling:** There's an equivalent: if you scroll down, `CLAUDE.md`. That's what Claude
looks for.

**24:12 —:** And no Fusion exports? Is there a Fusion API?
**—:** No, I don't think so. But for Fusion, it's generally been able to get the file if
you share the Fusion public share link. Then it can download it.

**25:38:** *[Both have become partial to Onshape; Sam notes that BYU Mars Rover uses it.
Conversation about a student club omitted.]*

## Part 4: Finding the current files (28:35–31:35)

**28:35 —:** 90° [?]. What are all the files that are required for this? Could we have
them in a single project?
**—:** That's a good question. We can start one.

**29:22 Sam:** We split it across so many places. This is mostly where all of it is: the
tap collar is here, the mounting plate is here. I think most of it is in here. This
baseplate…

**30:09 Sam:** I could make a folder with all of these. It's a mix of new and old parts:
some are in their original places, and half of them are just in the powder doser
folder. This is the baseplate we should be using, I'm pretty sure, and this is the
bracket we should use.
**Sterling:** How about this: we leave it in the current organization, but go to the
baseplate for now. It crossed my mind that there might be a shared version without
opening it. But if you go to the File tab: Share, file link, anyone, and allow
downloads.

**31:15 Sterling:** Then I think you might have to exit out of it. Put that on the new
issue that I made [#165?].

**32:36:** *[Personal conversation omitted.]*

**35:04 —:** "Agentic capabilities in [the] assistant." Oh my, they put an agent in an
agent, and it says it can do actions. I have no idea how good it is. When we started
this, we said it would be out of date in two months or less. That's something someone
else will have to check sometime. Part of me wishes I didn't feel compelled to look at
it, because if we look into it and it turns out to be meh, that's wasted time.

## Part 5: The parts list and the #170 prompt (36:40–45:36)

**36:40 Sam:** So we need the baseplate, mounting plate, auger, brackets and tap collar.
And the tap-collar base: I don't even know where that part is.

**37:29 Sam:** We have the tap collar that sits on this tap-collar base thing, and the
tap-collar base isn't in here. I think the AI did a good enough job at the end, so we're
still just using that part, from wherever it is. I'll have to find it. Maybe just make a
note of it instead of giving a link: tap-collar base, probably somewhere in a branch of
the repository.

**38:20 Sam:** I would love to have actual models of the stepper and the solenoid.
**Sterling:** Are you saying you have those, or you'd like to have them?
**Sam:** I'd like to have them. Here's the website for this one. And the servos.

**40:44 Sterling?:** [Claude can] model them to these specifications, the solenoid and
the stepper.

**42:16 Sterling:** Add a new line at the end and tell it to use its Onshape keys to
upload into your account. I don't know whether it'll be able to send it to the classroom
account, but we'll see. Tell it to try to upload to the Vertical Cloud Lab classroom, and
if not, to upload to your account.

**43:36 Sterling:** Then [it makes the] assembly using the Onshape API, once all the
files are in. One other thing: use the Raspberry Pi to access the Fusion 360 links and
download them.
**Sam:** What happens if you don't do that?
**Sterling:** It will often get blocked.

**45:15 Sterling:** Wait a second, before you hit enter: let's bring this into a PR. I'm
making a PR, and then let's post it there.
**Sam:** Is that 170?
**Sterling:** Yes. Go ahead and paste the prompt.
*[Sterling opens PR #170 at 20:02:33 UTC. Sam posts the Fusion 360 links and the
assembly prompt at 20:02:54 UTC.]*

## Part 6: Recent agent work in Onshape (46:25–49:52)

**46:25 Sterling:** Some recent things I was showing Michael: this was a couple of
prompts, and it was using Onshape. It made a GIF of it. Then it sent the prints to the
printer; Claude downloaded Bambu Studio. That was pretty cool.

**47:48 Sterling:** And another one: the arm needs a wrist camera. I've known that for a
while, and I've asked a couple of people to work on it, not here but elsewhere. It's
been a backlog item for a while. So this is the design, including the field of view. And
there's the top-corner camera as well: two cameras, one high-quality camera and one
wide-angle, with AprilTags.

**48:54 Sterling:** It took about four prompts. There were a couple of things where I
said, "Hey, that doesn't look very stable, because there isn't much of a mating face,"
or "Have you thought about using insert nuts for this?" Little tweaks like that. Both of
these were done exclusively through Onshape, which is part of why I've become pretty
partial to it.
**Sam:** It seems like the API really is like using the GUI.
**Sterling:** Yes.

**49:52 —:** So far it's saying it can't find the project. *[Probably the #170 session's
status.]*

**50:20:** *[Conversation about a capstone class omitted.]*

## Part 7: Auxiliary files (50:51–53:52)

**50:51 Sterling:** Maybe one more thing, quickly. If you could grab those other
auxiliary files, like the auger filling stand, and put them in a comment. You don't
have to ping Claude; just get the share URLs. And any other ones that you'd still
consider current.
**Sam:** The two smaller augers?
**Sterling:** Yes, augers like those would be good. They've been linked before, but I'll
make sure it looks at them now too.

**51:32 Sterling:** And then maybe the multi-doser?
**Sam:** That's all been moved over to Onshape.
**Sterling:** OK, cool. Let's just make sure that everything in Fusion 360 right now can
be accessed by Claude.
*[Sam posts the filling stand and the 3.32 mL and 9.18 mL augers on #170 at 20:10 UTC.]*

**53:18 Sam:** I think those are the only ones that really need to be shared. The old cap
designs are in [Fusion] too, but…
**Sterling:** If they're in Fusion 360, we can always go back to them. [Claude] would
probably get confused.

**53:52 —:** You know Todd Nelson? Seth Brewer is one of his research students, in the
machine design class [?]. He approached me and said, "I know you mentioned using Ansys
programmatically." Long story short, he gave me a prompt and a model, and I ran it
through this workflow that has Ansys, running every configuration through its API.
*[The transcript ends at 54:36.]*

---

## Glossary of corrected mishearings

| Raw transcript | Corrected |
|---|---|
| para tests | powder tests |
| Katie is filled / loading spots | it's filled / loading slots |
| bod plus opus medium | Opus with medium [effort] |
| zoom | Zoo (Zoo Design Studio) |
| leader versions can arrange so much around 1 cup | later versions can arrange several [channels] around one cup |
| how to excavate our idea | the powder-excavator idea |
| Sprint's like research thrust | sprints, or research thrusts |
| cloud, clotted, claw | Claude |
| Yammer, yamo | YAML |
| claw dot MD | `CLAUDE.md` |
| Copa instructions | Copilot instructions |
| on shape, onshade | Onshape |
| BYBC L1, BYU DCL | BYU VCL (Vertical Cloud Lab) |
| on on shape access key | `ONSHAPE_ACCESS_KEY` |
| Security. See you rich. Key, see Kurt Key | `ONSHAPE_SECRET_KEY` |
| tab color, tag color, app caller, map caller | tap collar |
| magic plate, boundary plate, mountain plate | mounting plate |
| bass plate, faceplate, today's play | baseplate |
| solaride, solar | solenoid |
| paradips or folder, paradoxer folder | powder doser folder |
| border guest | PR (pull request) |
| April 10X, April tennis | AprilTags |
| inset nuts | insert nuts |
| answers, advances (53:52) | Ansys |
| atomizer (08:14) | kept as heard; see MEETING-DECISIONS.md question 10 |
