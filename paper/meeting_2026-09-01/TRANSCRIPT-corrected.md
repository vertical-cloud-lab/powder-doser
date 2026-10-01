# Corrected transcript — powder-doser paper review meeting, 2026-09-01

Recording: <https://youtu.be/vZWPl0S0c_g> (unlisted, 1920×1080, 5522 s ≈ 1 h 32 m)
Wall-clock start 14:41:18 local. **Video time = wall clock − 14:41:18**, so every
timestamp below is also a valid `?t=` offset into the recording.

Present: Sterling Baird (remote), Sam Charles (sharing screen for 00:00–00:42),
with Sterling sharing from 00:43 to the end.

---

## How this transcript was produced, and what "corrected" means

The Teams recording produced a WebVTT file (`sources/teams_transcript.vtt`, 1152
cues) in which **every cue is attributed to a single speaker**, because the room
used one shared microphone. Speaker attribution below is therefore inferred from
content, not from the file, and is marked as such where it is not obvious.

The raw automatic speech recognition is noisy in three specific ways, and all
three are corrected here:

1. **Domain vocabulary is mangled.** Powder names, part names and statistical
   terms are consistently misheard. The substitutions applied are listed in the
   glossary below; each was verified against on-screen text in the recording, so
   these are corrections rather than guesses.
2. **Crosstalk is interleaved.** Two people speaking over each other are merged
   into one cue, which produces sentences that switch speaker mid-clause. Where
   the intent is recoverable, the passage is split; where it is not, it is left
   intact and flagged.
3. **The tail of the meeting is duplicated.** The tactiq export in particular
   repeats the same passage two or three times in consecutive blocks. Duplicates
   are collapsed.

Passages that are purely social (equipment chat, scheduling pleasantries,
camera-latency jokes) are summarised in one line rather than transcribed.

### Glossary of speech-to-text corrections

| Heard as | Actually | Evidence |
|---|---|---|
| "Zanthem gum", "Zanthem found me" | xanthan gum | on-screen figure labels |
| "sodium thalzonate" | sodium alginate | A2 figure, 10 mg/rev row |
| "ALSI 10MG", "ALSI 10" | AlSi10Mg | A2/R1 figure labels |
| "Game silica", "team silica", "feed silica", "fume silica" | fumed silica | A2/R1 figure labels |
| "beat factor" | feed factor | axis label in A2 and F1 |
| "buggy", "block scene" | block G, block C | protocol letters on screen |
| "Janie I", "Jen AI" | generative AI | context |
| "tap caller", "top column" | tap collar | Fig. 2b caption on screen |
| "Chris factor", "crest vector" | crest factor | R5c panel title |
| "predo front" | Pareto front | context (asking what's missing) |
| "the funeral" | the fume hood | context (bench relocation) |
| "few moves causing a bunch of migrations" | fume-hood move causing a bunch of vibrations | context; matches the documented 2026-08-20 baseline shift |
| "field phase thing" | three-phase thing | controller name used elsewhere |
| "the tab", "150 tabs" | the tap, 150 taps | E2 annotations read "78 taps", "148 taps" |
| "04590" | 0°/45°/90° | protocol C/B definitions |
| "1535 and 90" | 15, 45 and 90 RPM | protocol D definition |
| "60 seconds later" | 60 milliseconds later | he is reading "60 ms on" and self-corrects |
| "8% of the way" | 80 % of the way | context (what the AI pass achieves) |
| "easy posters" | Better Poster | he self-corrects on the recording |
| "fiction powders" | 13 powders | R1 table |
| "Dave" | data | context |
| "vibration matter" | vibration motor | context |
| "encounters", "patterns", "powers" | powders | throughout |
| "spring back some memories" | brings back some memories | context |
| "Kelly, we were talking about…" | (unrecoverable filler) | flagged inline |
| "the ******" (00:15:24) | masked by Teams' profanity filter; from context "the augers" | flagged inline |

One correction is **substantive rather than cosmetic** and is called out in the
body: at 00:09:10 Sterling reads the acronym **RSD** aloud and guesses it means
"root mean squared deviation". It does not — in the figures it is **relative
standard deviation**. His mis-guess is itself the evidence for the complaint he
is making, so it is transcribed as spoken and annotated.

---

## 00:00–00:03 · Opening and the overall plan

*(00:00–00:01 is setup: audio check, camera-latency small talk.)*

**00:01:20 — Sterling.** Lots of jargon. And we're trying to be as open source as
possible, so when it reads like this it becomes inaccessible. Even I found that.
What's the — "easy posters"? Better Poster, right. In light of Better Poster:
it's not that people in this industry don't know the jargon, it's that we all
struggle through it every time. We're not fluent in it; we figure it out.

**00:02:05 — Sterling.** The simpler we make it isn't just for people with no
experience in this field — it's also simpler for the people who have a lot of
experience. So let's make it better for everybody. I think it's a fine thing to
ask Claude: remove the jargon and make this better. I'll go line by line at some
point, but that's a fine Claude job. And I have a couple of notes I can put in a
comment.

**00:02:49 — Sterling.** This can get us maybe 80 % of the way to a pretty solid
paper. I can go line by line after that and make it a really good paper.

**00:03:10 — Sam.** For this meeting, let's just go through my notes and hear
what you think.

**00:03:20 — Sam.** So: jargon first, and I'll go line by line once it's in a
better spot. The rest of my notes are about graphs and graphics. There are two
places where we have graphics right now: the figures already in the paper, and
then the ones that are missing or wrong.

---

## 00:03–00:07 · The figures already in the manuscript

**00:03:34 — Sam.** Why do we have the timeline in it? We don't need that.

**00:03:45 — Sterling.** That's OK, we can take that out. I think I mentioned the
timeline at one point, just as a passing comment. What would probably be more
useful is *number of things as a function of time*, not a single pipeline
timeline. If we're talking about the generative-CAD piece, maybe it's OK — we can
throw whatever we want into supplementary information.

**00:04:16 — Sterling.** Generative-AI usage as a function of time. I think it's
cool that we have that data and we should use it. I run it for a couple of
projects — usually a few thousand dollars per project if you were to charge at
API rates.

**00:04:45 — Sam.** So some of these are helpful. I'm just going through what it
has and asking: what do I think could actually be helpful, and what would be
supplementary?

**00:05:00 — Sterling.** Like showing how it looks at 45 degrees — people know
what 45 degrees is. But what might be helpful is to **put a coordinate frame on
the jar**, something like that, so people know what axes we're talking about.

**00:05:20 — Sterling.** A cross-section is good. But this one isn't super
helpful — were we trying to talk about the tap collar? The generative-AI part of
the tap collar? I'm not sure.

**00:05:35 — Sterling.** And then here — yes. The design case studies. They walk
you through: this is how we did it, this is showcasing the kind of design
problems. That's helpful, we can keep some of those.

**00:05:47 — Sam.** And then this is fake data.

**00:05:52 — Sterling.** Which is awesome. I guess we hadn't pinged it yet to put
in real data. So this is still from back before we had it.

**00:06:05 — Sam.** And then I asked it to make some graphs based on real data,
so now we have those — that's in the comment.

**00:06:20 — Sam.** So we have graphics in two places: the stuff it already put
into the paper, which is mostly pictures and things that are legitimate, and then
the data figures.

---

## 00:07–00:10 · "I don't even know what metrics we're using"

**00:06:55 — Sam.** We talked about how the main way we interface with the
hardware is through Claude. To me that's sometimes scary.

**00:07:12 — Sam.** One thing I ran into: it's been super handy to just say
"Claude, run this and record this data" — but even when I thought I was doing a
good job of following up and knowing what it was recording, now that I'm trying
to write a paper and thinking about what graphs would be helpful, **I don't even
know what metrics we're using. What did we even collect?**

**00:07:40 — Sterling.** It's the same as the diameter-of-the-auger problem,
right? This should be second nature and I have no idea what we're talking about.

**00:07:50 — Sterling.** At some point we were saying: what data needs to be
collected for the placeholder figures? What would actually go in there? At some
point there may have been a disconnect. It became "collect the data" rather than
"make sure you're collecting the data *for that paper*", and showing lots of the
data getting added inline so we can spot-check it as it goes.

**00:08:30 — Sam.** When I asked someone "just off the top of your head, what
graphs would be helpful?", it was hard to come up with them, because I didn't
know what metrics would even be helpful here.

**00:08:50 — Sam.** So: some of these are really good, some are really confusing,
and there's a lot of jargon here as well. Like **feed factor** — it throws that
around. And it's been using **dose rate**.

**00:09:00 — Sterling.** Dose rate is probably what we put in, right? It's a
powder doser.

**00:09:10 — Sam.** And revolution **RSD** — do you know what that stands for?

**00:09:14 — Sterling.** Root mean squared… root squared deviation?
> **Annotation:** In the figures, RSD is *relative standard deviation*. Sterling's
> mis-guess is the point: two of the paper's own authors could not recover the
> term from the figure. Treat this as evidence, not as a definition.

**00:09:21 — Sam.** Basically it felt like it's saying "scatter". But this is not
a good use of an arrow either. Anyway — it uses a lot of jargon, and that's even
to me, who's been doing this for a while.

**00:09:45 — Sam.** This was interesting too. I'm pretty sure it's saying nothing
was dispensed. I get it, but that's not really a helpful way to say that.
**Don't put it on the graph** — just make a note, or show it as hatched. Like a
hatched bar.

**00:10:10 — Sterling.** Yes — strike through the text.

**00:10:20 — Sam.** These just seem to need a lot of work to be readable. But at
least it *is* the data. It does have the data.

---

## 00:10–00:17 · Figure A2 (feed factor across all 13 powders)

**00:10:40 — Sterling.** OK: food-safe versus the ones that are more
research-relevant. 10 milligrams per revolution of the auger when it's at 45
degrees — not considering the fill level.

**00:10:51 — Sterling.** The fill level does affect it, so this is probably not
for a fixed fill level.

**00:11:00 — Sterling.** We can go from 10 mg per revolution for sodium alginate
all the way up to 230. I actually didn't realise the AlSi10Mg would be the
highest-flowing of everything. But it's not that different from xanthan gum.
A lot of them are within some percentage of each other, except for these.

**00:11:30 — Sterling.** What was CMC like? Also kind of floury?

**00:11:40 — Sam.** Let me look back over Carl's videos. I have some videos where
I just had them in a transparent cup — that gave a much more tangible sense of
the powder. Pulling it out on the spoons: this one is this tall, this one is
this tall.

**00:12:18 — Sam.** So I want to know which of these you think are helpful, and
then I can clean them up and make them more readable. Or which ones you think
we're missing.

**00:12:35 — Sterling.** I think this one, **A2**, has good information in it
that we can display graphically. I think the use of colour to split the food-safe
surrogate versus the research-relevant ones is good — **we want to keep a visual
separation between the different types.**

**00:13:00 — Sterling.** We shouldn't be plotting any data for the silicon
−325 mesh, the brown rice flour, the fumed silica. We can optionally keep them on
the graph, but just as a strike-through. I think a strike-through of the text
would come across fine.

**00:13:25 — Sterling.** And I think we really do need to clarify in the caption
— it was putting the caption as embedded text in the figure. **Every figure.**
No matter how many times: keep it out of the figure image.

**00:13:41 — Sam.** I get it. It's all in one file, so it's helpful for it, but…

**00:13:55 — Sterling.** Having in there clarifications about other factors that
affect things — like the fill level — that weren't controlled for here. But the
raw data is available. And that might be where the Claude team can go through and
grab these data points.

**00:14:26 — Sterling.** What was the fill level when this was collected? I also
don't know if repeats were run on this. It seems like maybe not — it's not an
identical repeat of the 45-degree tilts.

**00:14:50 — Sterling.** We can try to get the data for what the fill levels
were. We should address that somehow, even if it's just in the caption.

**00:15:07 — Sam.** I think it's going to be hard to measure. I didn't really
control for that myself. It was up to pretty close to the top, but not totally at
the top. And some of them didn't have enough powder, so they were like half. So
it varies throughout.

**00:15:24 — Sterling.** Did you weigh the ******* before and after?
> **Annotation:** the word is masked by Teams' profanity filter; from context it
> is "the augers". The intent is: was the loaded auger weighed before and after
> each run, so fill level and total conveyed mass could be recovered?

**00:15:33 — Sam.** No, I didn't. Once I was done it was like — that would be a
good idea.

**00:15:53 — Sterling.** These ones were really hard to get anything out of.
These all fall in a similar range. Also this fumed silica is weird. Just don't
touch it, it's not going to work.

**00:16:15 — Sterling.** This one probably has something to do with it being
really jagged. Frankly, the AlSi10Mg probably flows so well in part because they
are particles for laser powder-bed fusion, which requires very high sphericity —
very spherical, uniform size distribution. You have to, to use them in metal 3D
printing.

**00:16:50 — Sterling.** So in retrospect that makes sense. I'm a little
surprised — I didn't think the silicon generally looks very spherical, but for
whatever reason the fine silicon is fine. We could have some commentary about
this.

---

## 00:17–00:20 · Figure F1, and where "blocks" became "test protocols"

**00:17:17 — Sam.** This one looks helpful if I really look at it. There's
probably a better way to do it. Oh — is this the lateral scatter? I don't know
how we would find that other than with a camera or something. That's what I mean:
**I don't even know what we're talking about here.**

**00:17:40 — Sam.** But I like having that distinction here. I like the way it's
set up. And revolution RSD — this "percent, block C". It keeps saying these
blocks. I think you had a sense of what that was; I never went back to the test.

**00:18:02 — Sam.** That was the other thing I was realising — I'm not sure where
all the blocks are. It's just the tests that I had. I had to make a script of a
bunch of tests. So the block is a different test, and obviously I know in my head
what each of them is.

**00:18:20 — Sam.** I wrote them. But that would be a good table to have.

**00:18:22 — Sterling.** Exactly.

**00:18:56 — Sterling.** They're better — it's like **test protocols**.
> **Annotation:** this is the moment that produced PR #150. The `@claude` comment
> asking for the table with "blocks" renamed to "test protocols" is timestamped
> 15:00:23 local = 00:19:05 video time.

**00:19:13 — Sam.** Maybe we come back to that. I like the idea of this graph. I
like the way it says it visually.

**00:19:35 — Sterling.** RSD might mean something else. That's the thing, right?
It produces so much content that it feels like "oh, we've been using this
terminology for the last three weeks" — and I probably should have read it more
closely, but I don't know what you're talking about.

---

## 00:20–00:22 · Figure E1, and the jitter complaint

**00:20:00 — Sam.** This one I like. I need to look again at what block it was
running, but I like the idea of: this is what we were shooting for, this is the
error, based on the same test for all the powders.

**00:20:25 — Sam.** And that is somewhat of a control problem now.

**00:20:33 — Sterling.** Right. We'll just point to it: **we used a simple method;
in future work we're going to do the calibration properly.**

**00:20:52 — Sterling.** Another thing — these are not any kind of range, so
these should all just be aligned perfectly. That's a specific type of plot:
it's **jitter**, in matplotlib and these plotting libraries. It's useful when you
have a lot of data points and you want to show a distribution without doing a
violin plot and without a bunch of overlapping points.

**00:21:25 — Sterling.** **We do not need jitter for three points.**

---

## 00:22–00:28 · Figure E2, block G, and what the closed-loop panel must answer

**00:21:34 — Sam.** And then this one — again, I'm not really sure what it's
trying to say. "Time to terminate the dose". As far as I know, that's: it stopped
the dose, and then the time for it to stop dispensing anything. And I'm not sure
what the taps are.

**00:22:05 — Sam.** Block G seems really important. Three doses of 1 gram per
powder, each marker is one dose, the grey rule spans the three.

**00:22:22 — Sam.** Annotations mean solenoid taps.

**00:22:30 — Sam.** So, brown rice flour — these ones again didn't do anything.
Why are they on here?

**00:22:45 — Sterling.** It's technically measured data, but it's noise. And
displaying it this way isn't helpful.

**00:23:00 — Sam.** Green is OK, yellow is overshoot, red is stalled.

**00:23:09 — Sam.** I like the idea of some of these. I like: when I stopped it,
how much time did it take to stop? Maybe that's a helpful metric — but is that
what it's talking about? I don't know. That's the thing.

**00:23:30 — Sterling.** "Time to terminate the dose" — this is just how long it
took to get there. We're trying to do 1 gram. Block G is the one that took the
longest: three doses of 1 gram, so this is how long it took.

**00:23:45 — Sam.** So it took a long time to dose CMC, and we didn't get there.

**00:23:52 — Sam.** So that's another thing. We got the revolutions at 45
degrees, but also when we ran the same — how accurate?

**00:24:10 — Sterling.** Maybe there's a way we can represent, either all in one
or separately, this idea of:

> - here was the **unique powder type**, and whether it's food-safe or
>   research-relevant;
> - here are the ones that **flowed fast**;
> - here's the **accuracy when we tried to be accurate** with this powder, under
>   the three-phase test procedure;
> - and the **total time it takes to get to that point**, which is basically a
>   function of the dose rate in a lot of ways;
> - and **what didn't flow well, and why it didn't flow well.**

**00:25:19 — Sterling.** We have some SEM images of the powders — throw those in.
Some characterisation data on some of this.

**00:25:43 — Sam.** So, many graphs that show all that. It depends — I don't know
how well we could show all that in one graph. Or we do a panel, or we keep them
as separate graphs. I'd be OK with that.

**00:26:05 — Sterling.** Part of it is: while we were looking at this one, it was
CMC, which obviously took a while to get there and it **stalled** — which I
assume means there came a point where it stopped dispensing anything. I'm not
sure why it would do that.

**00:26:25 — Sterling.** And then the question becomes: well, what was the
target, and how close did it get?

**00:26:50 — Sam.** So that's what it means by stalled — we did get somewhere.
But I don't know why it would stop there.

**00:27:00 — Sam.** I think it's back to the three-phase thing — it can't go back
to earlier phases. Once it gets to the tap phase it's just going to keep tapping,
with that little pocket in the front. It just keeps tapping.

**00:27:15 — Sterling.** CMC here had 148 taps and still didn't get there.

**00:27:30 — Sterling.** But again, that's the controls problem. And so I think
it's still meaningful to have this heuristic test and data from it. If we take
this heuristic, people want to know the performance of it. Even though we're
sectioning off the more advanced things for Will, **people will read this paper
and they want to know: can you dose it? How fast? Can you be accurate?**

**00:27:52 — Sam.** And it's helpful for me to remind myself that we're looking
for graphs that **showcase the powder doser, not the powders.**

---

## 00:28–00:29 · Figure C2

**00:28:30 — Sam.** This is really helpful, I think. It's cool to see: OK, it's
an auger, it's spinning, and it falls out, and it falls out. And this is how you
can see how the powder is coming.

**00:28:55 — Sterling.** It's never really continuous. Even the most continuous
one is still not.

**00:29:10 — Sterling.** I like that one. **I like C2.**

---

## 00:29–00:36 · Walking the test-protocol table (audio only)

> **Screen note:** from 00:29 to 00:36 Sterling is reading the protocol table on
> his own machine. The **shared** screen still shows the candidate-figure comment,
> so the screenshots in this window do not show the table he is describing.

**00:29:14 — Sterling.** This is in the supplementary information. That seems
like a pretty good one.

**00:29:20 — Sterling.** Protocol A — we'll stop saying block. Nothing was
varied, it's a balance baseline. Tilt at 45, eight reads. It's trying to get the
noise floor.

**00:29:45 — Sterling.** Static hold: 0/45/90, hold for 15 seconds, no actuation.
So just looking at gravity. Eight trials for A, three trials for protocol B.

**00:29:55 — Sam.** If you're holding for 15 seconds at a time but you're not
doing anything between them — is that one?

**00:30:10 — Sterling.** It says three trials, I guess because it's 0/45/90. I
don't know if it's three trials. It might be that it goes back to its normal
position and then back up to 45. Good question — that's something to figure out
about the test.

**00:30:35 — Sterling.** Rotation yield: this is the 0/45/90, six revolutions,
30 RPM. Revolution-to-revolution spread. Feed factor and precision at each tilt.
So: for the first revolution, this is how much mass was delivered; for the
second revolution, this is how much mass was delivered.

**00:31:15 — Sterling.** The revolution-to-revolution spread seems to be what
it's trying to capture there. **I'd rather just see error bars.** Or actually the
individual data points, maybe.

**00:31:31 — Sterling.** Looks like 18 trials for this one. Again, we really need
to figure out **what a trial means.**

**00:31:50 — Sterling.** Speed sweep: 15, 45, 90 RPM, tilt at 45, three
revolutions, streaming the balance. Mass flow rate versus rotation speed.
Within-revolution pulsation of the discharge from the streamed mass trace.

**00:32:20 — Sterling.** On block D, streaming balance polls during three
revolutions at 15 RPM. It noticed the pulsating behaviour.

**00:32:50 — Sterling.** Tap yield: tilt 0 and 45, eight trials. Doing a re-feed
— a revolution, because tapping removes that. So a 360° rotation, one solenoid
tap, 60 milliseconds on.

**00:33:20 — Sam.** I guess you send a signal to turn the current on in the
solenoid for some time and then drop it, so it's a 60-millisecond pulse.

**00:33:41 — Sterling.** And that re-feed is logged separately. 32 trials.

**00:34:00 — Sterling.** [Protocol F] Obviously, nothing. I still want to get
that back on at some point.

**00:34:15 — Sam.** Priorities. We have priorities right now.

**00:34:25 — Sterling.** Closed-loop dose: three doses, 1-gram target, three-phase
controller. Dose error, time to dose, and the breakdown of bulk, fine and tap.

**00:34:50 — Sterling.** And this says trials — three doses. So maybe "trials" is
the generous interpretation: it ran this procedure 18 times per powder.

**00:35:10 — Sterling.** But for C it's six revolutions at 0/45/90 each, so
that's 18 total. Yeah, I think that's it. So the less generous interpretation.

---

## 00:35–00:43 · The new asks

**00:35:51 — Sterling.** So from that information, do you think there's anything
we're really lacking? A Pareto front of…

**00:35:55 — Sterling.** Wait, hold up. Not related to that so much, but: **a
scatter plot of dose error versus time to dose.**

**00:36:14 — Sterling.** Do we have that already? Is that this one? No, that
doesn't have time to dose. So basically this plot, but with time to dose. And
instead of an axis for the powders, we'd have unique symbols — some way to
differentiate within the chart itself. So this would be **dose error versus time
to dose, and that would only pull from G.**

**00:37:01 — Sterling.** Move that table onto the main thing.
> **Annotation:** "that table" is the test-protocol table, i.e. Table S2 added in
> PR #150. Sterling wants it in the main text, not the SI.

**00:37:19 — Sterling.** We kind of want to capture the effect of each, isolated.
We've got **tilt, speed and tapping** — isolate the effects of those.

**00:37:45 — Sterling.** Do we have something like: one tap for this powder
typically gives this much, and here's the spread?

**00:38:15 — Sterling.** Oh yeah, that's right. **We only did it for one mass.**

**00:38:26 — Sterling.** I figured if we talked about that one, doing it for a
couple of different target masses. Like 20 milligrams, 1 gram, 5 grams — the
target dose. But that might be more Will's, so we may have sectioned that out.

**00:39:19 — Sterling.** *(reading aloud)* "No, you cannot compute the CV from
n = 1." Thank you. Well — condescending. It's often insulting. Were you trying to
insult my intelligence?
> **Annotation:** this is a comment on the *tone* of the AI-written analysis, not
> on the statistics, which are correct. It is an actionable style note.

**00:40:19 — Sterling.** For the ones that didn't dispense, it's a question of:
maybe we need to look at the auger geometry. Because if we had an empty cylinder,
we'd expect some powder to flow if we tilt it at 90 degrees and spin it and tap
it. So **that one becomes more of a design thing.**

**00:41:07 — Sterling.** So this, for example: milligrams per solenoid tap, and
the feed factor at 45.

**00:41:48 — Sterling.** Things that feed at approximately the same rate with
revolutions can have a dramatically different **tap response**.

---

## 00:43–00:48 · The dose-rate EDA: coverage, and the missing block G

**00:43:10 — Sterling.** Let me do a screen share.

**00:43:30 — Sterling.** *(reading)* "Summarize the totality of the data that's
been collected… evaluating effects of different parameters on the
semi-instantaneous dose rate. Do exploratory data analysis." About 64 grams of
powder moved through the auger in the characterisation blocks, and another 22
grams in doses.

**00:44:10 — Sterling.** 19 runs, 13 powders, 1200 measured trials. That's pretty
cool. A little more than that for the streamed balance polls. 36 closed-loop
doses.

**00:45:25 — Sterling.** This is just showing how many trials were run. So it's
basically saying we got all the data, **except that we don't have G for salt,
sodium sulfate, the silicon, fumed silica, barium chloride, or the AlSi10Mg.**

**00:45:55 — Sterling.** I think it was because of the fume-hood move causing a
bunch of vibrations and things, so it just had to pause. **If we were to go back
and collect some more data, filling in these would be the completeness step for
the manuscript.**

**00:46:14 — Sterling.** What do you think about redoing the three-phase dose test
for the other ones?

**00:46:30 — Sam.** I don't remember why it didn't happen, but out of literally
1200 measured trials… We still have the augers that are filled. Is it easier to
just clean up? OK.

**00:46:50 — Sam.** It's still in the fume hood and stuff. Thank you for turning
on the scale.

**00:46:57 — Sterling.** Do you know why it turned off? I don't know if it turned
off at some point today. Not great. It would be fine if Claude could send a ping
and wake it up.

**00:47:10 — Sterling.** Is it expected that the scale would turn off after some
period of time? Sam mentioned there was no real indication as to why it was off.

**00:47:33 — Sam.** Yes, I can rerun those this week.

**00:47:40 — Sterling.** That's interesting too — how much was dosed in total.
9 grams of the AlSi10Mg. Because these tests weren't at a threshold of "dose as
much"; just see how much gets dosed.

---

## 00:48–00:53 · R2 and R3: the rate ladder and tilt

**00:48:15 — Sterling.** Milligrams per second. **Dose rate spans three decades
under one frozen parameter set** — block C, 30 RPM, tilt 45 degrees, mean of six
single revolutions.

**00:48:56 — Sterling.** It's including this as one of the orders of magnitude,
but it can vary based on revolutions specifically.

**00:49:15 — Sterling.** Tilt: 0/45/90, mass per auger revolution. In general,
90-degree tilt gives more dispensed mass. **How much of the flow is gravity, not
the auger?** That's actually interesting. Gravity assist.

**00:49:41 — Sterling.** For some of these, if you put it at 90 it wouldn't just
start flowing. It takes a long time to stop, but they do stop.

**00:50:05 — Sterling.** So gravity assist: when you put sodium alginate at 90
degrees, it dispenses 15 times faster than at 0.

**00:50:15 — Sterling.** **This shouldn't even be on there.** Fumed silica and
CMC — fumed silica is 2× faster? I think that's probably because it was measuring
the noise floor on the scale and it happened to be greater than one.

**00:50:40 — Sterling.** I'm just looking at silicon −325: there's nothing at 0
and 45, but it's saying it conveys a little bit at 90 degrees.

**00:51:28 — Sam.** So it sounds like the silicon — that's kind of interesting.
"Hey, we couldn't get any of this out unless we tilted it." That's kind of the
flip side of things.

**00:51:45 — Sterling.** Is there something that wouldn't work at 90 degrees that
would work at another angle? **That's a story.**

**00:52:31 — Sterling.** It's saying the ones that need gravity are the cohesive
ones. I'm seeing that a little bit here for white rice flour. **Keeping in mind
this is log scale** — it has a bigger effect in relative percent than it does in
magnitude. These ones are still more, in absolute terms.

---

## 00:53–01:00 · R4: speed, and the two regimes

**00:53:46 — Sterling.** Six times the speed buys about three times the rate.
It did do different speeds — 15, 45 and 90 RPM.

**00:54:10 — Sterling.** Very interesting. Spinning it faster — that's not
looking so good, but it's the most interesting thing in the data.

**00:54:30 — Sterling.** *(on the AI's writing voice)* If you think of Claude as
a cynical robot that's kind of sarcastic and salty towards you and very lazy —
"oh, OK, human, I don't want to do that" — it totally changes how you read
things. At least it did for me a year ago. "I'm so sorry, I slaved for hours on
this." You ran for 20 minutes. What do you mean?

**00:55:14 — Sam.** It's probably good for my communication skills. I have to
tell it exactly what I want — there is no way to misunderstand what I'm saying
here. You've got to be really clear.

**00:55:50 — Sterling.** OK: flights fill by time. Mass per revolution relative
to 15 RPM.

**00:56:01 — Sam.** So when it said 15, they all… and 45 is how much differently
they dispense versus 15. Wait — is it saying these ones dispensed *less* at
higher speeds?

**00:56:20 — Sterling.** By time, not by turn. Because it's per revolution, not
per second. So you're dispensing less mass per revolution at 90 RPM, but you're
doing more revolutions in the same amount of time.

**00:56:46 — Sterling.** Six times the number of revolutions, but each revolution
is only getting maybe 50 % of what the others were.

**00:57:05 — Sterling.** And it's calling those regimes: **fill-limited versus
mobilisation-limited.** So the ones below are fill-limited, everything above is
mobilisation-limited. If it's fill-limited, it just doesn't have time to get to
the front.

**00:57:31 — Sam.** Like the auger's moving faster but the powder isn't reaching
it yet. You don't have enough friction or gravity.

**00:58:15 — Sterling.** I guess it doesn't matter either way in terms of the
result, but fill versus mobilisation does tell you something about the powders —
visually, what's happening inside.

**00:58:42 — Sterling.** "Faster rotation mobilises powder rather than starving
it." Maybe because it's cohesive, you have these bigger chunks and globs that get
rattled through.

**00:59:00 — Sterling.** Some of this could factor into Will's work with the
optimisation. Maybe we have ways of describing powders that can help us learn
more about their characteristics. That's what I was asking before — whether there
was a Reynolds number for powders, and it said no.

**00:59:23 — Sterling.** The fact that you could change the speed of the auger
and maybe be able to tell whether or not it's a cohesive powder — that's kind of
cool. We could make note of that in the paper, going into future work: **this
data can also tell us things about the powder.** For example, by changing the
revolution speed we're able to distinguish between cohesive and non-cohesive
powders. That could be a good future-work call-out.

---

## 01:00–01:06 · R5: depletion, one slug per revolution, crest factor

**01:00:23 — Sterling.** Depletion control. This is good. Block C, six consecutive
revolutions at fixed conditions, mass declines by a median 1 % per revolution.
Actually — basically this is the fill level. It was looking at the effect of fill
level over time. Not entirely fill level maybe, but probably mostly.

**01:01:05 — Sterling.** Semi-instantaneous rate, one slug per revolution.

**01:01:20 — Sterling.** Block D streamed balance polls, tilt 45 degrees, top row
is 15 RPM, dotted lines mark revolutions. So revolution one took about four
seconds — about four seconds per revolution at 15 RPM.

**01:01:50 — Sterling.** Discharge locks to the revolution: median autocorrelation
peak at 4 seconds. Pulsation is real at 15 RPM, but 45 and 90 RPM are
under-sampled.

**01:02:20 — Sterling.** I think it's good that it shows the revolutions. You
could just show the revolution, but it's kind of a visualisation aid, so you can
clearly see each of these.

**01:02:43 — Sterling.** Now, here's something. NaCl — not much accumulating
until we've already done a full revolution. It's like leading edge versus trailing
edge. Same thing here for xanthan gum — which I thought flows so smoothly — before
the first revolution is even complete we have something. Is that just where it
happened to be?

**01:03:29 — Sterling.** You can't guarantee they'll start at the exact same
place, with the exact distribution of powder based on the previous dosing runs.
So that gets tricky: **how do you reset an experiment? What's a reset?** But also,
when you're actually dosing you're not going to reset every time. So how do you
account for the current state of the system?

**01:04:09 — Sterling.** There's a repeating pattern within each of these that
corresponds to that. I wonder if part of it is the timing — if we ran it at 1
RPM. And maybe this evens out because the powder is settling. I wonder how much
of this is the powder bouncing. I wonder if we'd get a stronger reverberation —
that would help with this too.

**01:04:54 — Sterling.** Pulsation at 15 RPM, crest factor: 95th-percentile
instantaneous rate over the mean rate.

**01:05:38 — Sterling.** It's trying to do some fancy signal processing. Crest
factor — the ratio of a waveform's peak amplitude to its root-mean-square value,
showing how extreme or spiky the peaks are.

**01:05:55 — Sterling.** All right, some measure of spikiness. **I don't think we
really need to hear about that.**

---

## 01:06–01:09 · R6: don't put every knob on one axis

**01:06:20 — Sterling.** Maybe this goes to say: **let's not put everything on one
axis.** Or at least not in this way. I get what it's saying — one revolution at 0,
one at 45, one at 90 — but it's confusing.

**01:07:12 — Sterling.** I'm pretty confident on this: let's not have this kind of
totality graph with **powder type as a major axis**. We're not talking about the
powder type; we're going to talk about the powder doser.

**01:07:45 — Sterling.** "Nothing flows on its own. A 15-second static hold with
no actuation produced no mass change." One exception, silicon.

**01:07:59 — Sterling.** Across every powder and every tilt, a 15-second static
hold with no actuation produced no mass change. Does it mean that it cleared its
own run's noise floor? OK.

**01:08:22 — Sterling.** Clean shut-off. One to 12 % of a revolution.

**01:08:30 — Sterling.** One thing we didn't do, if we really wanted to get into
the fine details: what happens if we **pause** it? One revolution, pause, and go
again — or pause it half a revolution. That would resolve what's happening inside
the auger.

**01:08:55 — Sam.** Transparent augers — that we've got a bunch of — would be
awesome. Technically we do the resin prints; they have some very transparent
ones. You need to cure inside.

---

## 01:09–01:16 · R7 firmware defect, and the gear-ratio correction

**01:09:20 — Sterling.** A firmware defect the EDA turned up. Block D
over-rotates by a factor that stepped mid-campaign.

**01:09:49 — Sterling.** It's saying on August 13th to August 19th it rotated more
than it used to for the same commanded rotation. When it commanded 3 revolutions,
the actual was a little bit more than that prior to that. But then at some point
it started really overdoing the rotation — the week of August 13th, somewhere
between August 13th and the 19th or 20th.

**01:10:50 — Sam.** You're saying that's a factor of the fume hood or something?

**01:14:31 — Sterling.** OK, and then when it corrected it, it makes more sense
for milligrams per revolution.

**01:14:50 — Sam.** One thing I keep forgetting to change: **it thinks that the
stepper motor and the auger gear are the same ratio.** Specifically, there have
been a couple of times where it asks "what's the ratio?" and it's one-to-one.
It's really not. So I need to let it know that, and I can update the data.

**01:15:14 — Sam.** That'll affect everything that says revolution. **When I
commanded three revolutions, that was one revolution.**

**01:15:25 — Sterling.** It could be inconsistent — sometimes it's accounting for
that and other times it isn't. So you need to let it know there is a difference
there.

> **Annotation — verified against the repository.** This is correct and it is
> larger than it sounds. `cad/auger-geared/stepper-pinion.scad` states in its own
> header: `Gear ratio (reduction) = Z_g / Z_p = 48 / 16 = 3.0 : 1`, and
> `auger-core.scad` sets `gear_teeth = 48` against `pinion_teeth = 16`. The
> firmware (`hardware/test-module/firmware/main.py`) computes
> `steps_per_rev = STEPPER_FULL_STEPS_REV * STEPPER_MICROSTEPS` with **no gear
> term**, so a commanded "revolution" is one *stepper* revolution = **one third**
> of an auger revolution — exactly matching Sam's "three revolutions was one
> revolution". Separately, `paper/main.tex` currently states the spur pair is
> **2.25:1**, which contradicts the CAD. Both must be fixed.

**01:15:39 — Sterling.** There were no changes in parts, right?

**01:15:45 — Sam.** I don't think there were any parts swapped out.

---

## 01:16–01:18 · R8: variance decomposition

**01:15:55 — Sterling.** Which parameter explains the rate? This is going for a
bit of a feature importance. Powder affects it a lot. Tilt angle has a high
effect. Powder-and-tilt interaction, not as much.

**01:16:20 — Sterling.** I think it's saying which knob specifically is doing
this, and what the interaction is. **I wouldn't have split that up.** It'll show
both — split up individually, and then also show cross-correlations.

**01:16:45 — Sterling.** Nested decomposition of log₁₀ milligrams per revolution
over all resolvable block-C revolutions. I know about powder identity, so that's
kind of all I care about; I care more about the tilt interaction with the others.

**01:17:10 — Sterling.** This is reasonable — like, randomise the order.

---

## 01:18–01:23 · New protocols H and I, the U of U target, and bench provenance

**01:18:21 — Sterling.** If you were to go back and collect some more data — if we
had an **H and an I** that was like 100 milligrams… I don't know, like 50
milligrams, 200 milligrams, 1 gram. I don't know if we want to go up to 5 grams
because we're going to have to be refilling it. I don't even know if we have 5
grams to dispense.

**01:19:02 — Sterling.** Which ones are we pretty limited on? One of them is a
really small bottle.

**01:19:15 — Sam.** It's not the fumed silica, it's the — sorry, sulfate — this is
silicon. I think it's silicon 110/200.

**01:19:40 — Sterling.** So if we added an H and an I, where H is **50, 200 and
1000** milligrams. That feels OK for capturing different ranges. It doesn't
capture the University of Utah range quite as well.

**01:20:09 — Sterling.** And it's in the fume hood for a lot of these, and there's
maybe a **50-milligram noise threshold** on some of it, so in some sense it's a
little safer to go a little higher, given the fume-hood situation.

**01:20:25 — Sterling.** What point do they need to be dispensing at?

**01:20:40 — Sam.** They can be smaller than that — like 1 milligram.

**01:20:47 — Sterling.** *(reading issue #117)* "Can the current system reliably
deliver 0.1 to 10 milligrams of a powder to a small reaction vial or 96-well
plate?" **No.**

**01:21:05 — Sterling.** And I think we could probe that more. But first, I think
we want more of Will's stuff in place before we spend a whole bunch of time on
it. Second, we'd want really good **vibration isolation**. And third, probably
**new auger dimensions** — because I think it'll be too hard to do until you
change the dimensions.

**01:21:35 — Sterling.** I think 50 milligrams is already kind of a — for the
noise. We're only going to be able to say so much.

**01:21:55 — Sterling.** It might be worth trying to differentiate — and this
could just be in supplementary information — **when it was in the fume hood, when
it was in the lab, and when the box went over it.**

**01:22:18 — Sam.** We might be able to get that from the live streams. The box
was only a few seconds.

**01:22:35 — Sam.** All of the food-safe powders were in the lab, and all of the
non-food-safe were in the fume hood.

**01:22:45 — Sterling.** I'll let it know that for sure. I think it does know,
but…

---

## 01:23–01:25 · Multi-doser aside

**01:22:56 — Sterling.** Did you see the new design? I watched the video. I like
it a lot. It's still got a ways to go, but it's something.

**01:23:20 — Sterling.** Maybe it's useful to have a **weighing station** as well.
Something that could push it up, check the weight, then dispense, then go back
and check the weight again.

**01:23:41 — Sam.** I guess you just put a load cell on the end of it. It's
attached to the arm, so it's not the full weight of it — you'd have to correct for
it, but the raw data…

**01:24:10 — Sterling.** You can put a current measurement. There are some ways to
get it. I think a load cell would probably be the most straightforward.

**01:24:25 — Sam.** I just want to measure the signal; I don't want to have to
redesign. But a load cell might not be too bad. I like that idea.

---

## 01:25–01:32 · Plan, timeline, and how to hand this back to Claude

**01:24:46 — Sam.** This is a lot of graphs. Do you want to cut this down a bit?
I'll run some more tests. I'm a little anxious to get this out there.

**01:25:05 — Sterling.** I'm with you. Ideally if we can get it back with
revisions — more like **November** would be awesome.

**01:25:20 — Sam.** I think I can do these tests this week. Hopefully not
tomorrow — Thursday.

**01:25:30 — Sam.** Are there any of these that you're like "put this in", or
should we run the tests and then meet again and talk?

**01:25:45 — Sterling.** I think we should try to get it mostly finalised, where
all we're doing is just filling in some of that.

**01:26:00 — Sam.** What do you think about the 50 milligrams and the 200
milligrams? We could wait — maybe the reviewers come back with that as a request
and we say "OK, done".

**01:26:15 — Sterling.** If it's a couple of months, then we'll have to factor in
that the powder will have been sitting. We could run those tests because we care
about it, and it'll affect things for Will as well, to have that as a baseline.
One way or another I think we will collect that data.

**01:26:40 — Sterling.** We're also going to put the **preprint** out there. I
think that would be a strength for the preprint, as people are looking at it. It's
a natural question they'll be asking: "well, if I want 50 milligrams, can I get
it? And how long does it take? And how accurately did it get there?"

**01:26:55 — Sam.** I'll run it on Thursday.

**01:27:15 — Sam.** So you gave me this list of "we need graphs to show unique
powder type, which ones flow best, how accurate, the time to get to that dose
point". What's the best way to get the graphs into the paper? Should we make this
list of graphs that we want — this versus this, this versus this — or should we…?
I'm a little overwhelmed. We have a lot of graphs here and they require a lot of
changes. So I'm wondering if I should just say **"make a list of, like, we want
these eight figures — look at the data and give me these eight figures."**

**01:27:41 — Sterling.** I'll take the transcript recording and have it try to
summarise that. If you could also send me your notes, I can include that in the
prompt. Then we'll review the prompt, so you have it right in the prompt to do
more graphs. We'll take the transcript, we'll take your notes, we'll have Claude
merge that into a cohesive set of things. We'll double-check it. I think then
we'll just let it run.

**01:28:10 — Sam.** I'll send this to you, and then we'll have it do that once
I've run these new tests so that it can include that data as well.

**01:28:20 — Sterling.** We can do all this now, and then when the new data comes
in we'll just say "hey, here's the new data".

**01:28:35 — Sterling.** After that it might make sense for you to do a similar
process — maybe with Will and Luke involved too — of what I talked about with the
tensegrity project: screen-record start to finish, go through it, tear it apart.
Collect that from everybody, update it, do a couple of iterations. Sometimes it's
not until the third iteration that you get something good.

**01:29:20 — Sam.** Then we're just going to bring this into **Overleaf**, make
any final edits, and here's the PDF — then we'll submit.

**01:29:35 — Sterling.** That sounds good to me. I feel like I have a good plan
for how we're going to get the graphs and how we're going to get the paper.

**01:29:45 — Sterling.** And I just really have to say — you ran 1200 experiments.
That's pretty cool. And most of it was automated.

**01:30:05 — Sam.** I ran it in these batches. We ran 13 powders, and each of
those was about 100 trials.

**01:30:40 — Sam.** For the semester now, I think I can do about 10 hours a week.

**01:31:18 — Sam.** Trying to get this out as soon as possible, and then this
semester trying to get the multi-doser up and running after this.

**01:31:35 — Sterling.** The concept is really there. You already have the
prototype with the unit. There are a couple of units to work out.

**01:31:50 — Sterling.** I'll send this list to you — I'll just do it right now.
