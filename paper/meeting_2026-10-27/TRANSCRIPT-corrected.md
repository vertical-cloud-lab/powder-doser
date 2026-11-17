# Corrected transcript: 27 October 2026 meeting (Sam Charles, Sterling Baird)

Sam and Sterling met in person to restart the abstract and plan the manuscript's
figures. The recording is "Oct 27 at 2-21 PM - Sam, doser manuscript.m4a", a phone
recording in Sterling's OneDrive, shared on
[#97](https://github.com/vertical-cloud-lab/powder-doser/pull/97#issuecomment-6482321642).
It runs 34 min 31 s and, going by its file name, starts at about 14:21 MDT (20:21 UTC).
Times below are minutes and seconds into the recording.

The abstract prompt Sterling dictates at 06:43 started the Claude Code session archived in
[`../abstract_2026-10-28/`](../abstract_2026-10-28/README.md).

## Main points

- **Abstract (00:00–07:57).** After comparing the TMS 2027 abstracts with the Utah AI
  Convergence abstract, they chose the Utah one as the new starting point for the DD
  abstract: past tense, the same structure and flow, and no unnecessary details (06:43).
  Two comments while reading it:
  - Drop the cross-contamination target. The design prevents cross-contamination, so
    point to the multi-doser instead (02:49).
  - Say between which dates and with which models the AI work was done. That also shows
    how quickly the project moved (03:40).
- **Figures to make (07:57–28:50).** The list was written up during the meeting in two
  colours, green for the main text and blue for the SI (25:27). No photo of it is in the
  repository.
  1. Fig. 1: the real, assembled doser, with an exploded view (08:24) and callouts, as one
     large image (24:55, 25:37). Commercial systems, as on the Utah poster, probably stay
     out, because using their images (METTLER TOLEDO, for example) may not be OK (08:46).
     A photo of powder in the beaker on the balance would be nice (23:09).
  2. AI-made parts beside the human redesigns, for example the original AI tap collar and
     the redesign (10:40). Show the final version, which may need a new photo (12:13).
  3. A timeline of key designs: AI along the top and the engineers along the bottom (13:25),
     labelled with the agent and model used (13:44), with the hand drawings included (24:30).
     It can also carry the "AI version, then redesign" story (17:56).
  4. The dosing stages (the three-phase procedure) as keyframes pulled from the videos
     (18:32–19:45). These could sit beside the feedback block diagram and the Claude ping
     that starts a dose, taken from a phone screen recording or a GitHub snapshot
     (22:03–23:06).
  5. All the dosers lined up, with callouts of what is inside each one (23:30). It's
     "mainly shock value", so it goes in the main text, perhaps as an inset (27:16).
  6. Loading, installing and swapping augers (20:09). Basic use goes in the main text;
     instructions and adjusting the height go in the SI (26:32). Will's modular stand is
     laser-cut, so it could be cut from one large sheet of wood for other labs (20:52).
  7. The tool comparison (CADSmith, Zoo and the coding agent) stays, as text in the main
     text and with its images in the SI (15:50–16:53). The mounting-plate gap case is
     optional (17:05).
- **The current results figures (28:52–33:02).**
  - Fig. 3 is fine. It and Fig. 4a are similar, but both can stay (29:31).
  - Fig. 3c's slow-versus-fast split and its revolution-to-revolution variation may not be
    needed (29:46).
  - Fig. 4a works better as a table, perhaps in the SI (30:33).
  - Fig. 4b should show every powder, not only the six whose tap increment exceeded twice
    its standard error. A bar graph of mass per tap with error bars would also work
    (30:50–31:49).
  - Fig. 5d (time per dose) suggests a link to the y-axis that isn't there. Drop it, or
    give the times in the text only (32:03–32:50).
- **Next steps (33:08–34:31).** Claude first makes all the candidate figures for review,
  then builds the paper, probably in a new PR (33:18, 34:10). Sterling thinks the current
  draft is "too locked into its own version" (33:39). Sam will write the list down and
  edit the manuscript from there (34:12).
- **Possible misreading of Fig. 6 (24:06).** Fig. 6 pairs Sam's hand sketch of the
  multi-doser carriage with his own Onshape model. In a paper about AI-modelled parts, a
  reader may take the pair as "the drawing, then what the AI made". Sam suggests showing a
  drawing he gave the AI beside the AI's model instead.

## How this was made

- **Audio.** Mono AAC at 48 kHz, downloaded on the GitHub runner from the share link. The
  audio is not in the repository.
- **Transcription.** faster-whisper 1.2.1 with Whisper large-v3 on the runner's CPU: int8,
  batched (batch size 8, beam size 5), Silero voice-activity filter, word timestamps, and a
  hint list of names and tools. The 27 min of speech took 21 min. A second large-v3 pass
  (sequential decoding with a context prompt) went over 18 unclear snippets. Where it
  heard more, its reading is used. Where the two passes disagree, both are given or the
  words are marked "[?]".
- **Speakers.** Voice embeddings (SpeechBrain ECAPA) on 1.5 s windows were clustered, and
  the eigengap shows two voices. The louder voice dictates the prompt to Claude at 06:43,
  so it is Sterling, nearer the phone; the other is Sam. Short replies ("Yeah", "OK") are
  shorter than the windows, so those labels come from context. "?" after a name marks a
  guess.
- **Corrections for intent.**
  - Passages read aloud are given as notes that quote the source: the Utah AI Convergence
    abstract (branch `abstracts/utah-ai-2026`, copied in
    [`0_utah_original.md`](../abstract_2026-10-28/0_utah_original.md)) and the dictated
    prompt (prompt 3 in the [session log](../abstract_2026-10-28/transcript.md)).
  - Misheard names and terms are fixed; see the glossary at the end.
  - Fillers and strings of "yeah" are trimmed.
  - Words in [brackets] are added for sense, and "[?]" marks words that could not be
    recovered.
- **Nothing left out.** The recording has no personal conversation, and no credentials
  were spoken.
- **Reproducing it.** The scripts are in [`tools/`](tools/). The uncorrected Whisper turns,
  with the machine speaker labels, are in
  [`TRANSCRIPT-whisper-raw.txt`](TRANSCRIPT-whisper-raw.txt).

---

## Part 1: Which abstract to start from (00:00–07:57)

**00:03 Sterling:** *[Reading the titles from Claude's reply.]* "An Open-Source, Low-Cost
Powder Doser Designed with Agentic AI and Generative CAD for Autonomous Alloy Discovery."
And then the TMS abstract… Oh, wait. [The] reason [it] only gave me the one of the
[three]… *[Claude's first reply quoted only Will's TMS abstract, the one confirmed as
accepted. Sterling then asked for the other two.]*

**00:40 Sam:** "…Generative CAD for Autonomous Alloy Discovery." [And the manuscript:]
"An open-source, 3D-printed auger powder doser designed with generative artificial
intelligence." So this one's got dumbed down.

**Sterling:** Yeah.

**Sam:** I don't want to, like, dumb it down.

**00:49 Sterling:** Yeah. Like, jargon… "jargon" doesn't mean [dumbing it down]. I've
found it works OK to say "non-domain-relevant jargon". I think that's helped a bit,
because [otherwise] it's like, "oh, the audience is [lay people]".

**01:04 Sam:** [It's not] just lay people in this, but it is, like… [?]

**01:12 Sterling:** And then there's this one. Oh, right, that one's more tied to the…
That one's Luke's: "Agentic Systems Design of an Open-Source Powder Doser for L-PBF
Feedstock Research: CAD, PCB, and Firmware". So I think we can stick with maybe the Utah
AI Convergence one.

**Sam:** Yeah, this one. Yeah.

**01:31 Sam?:** Um, the title of that abstract…

**01:35 Sterling:** The title… Maybe we read the abstract.

*[Sterling reads the first paragraph of the Utah AI Convergence abstract aloud, from
"Additive manufacturing of aerospace structural alloys depends on rapid, reproducible
exploration of powder feedstocks…" to "…L-PBF of aerospace alloys."]*

**02:27 Sterling:** "Hardware targets…" OK, so that's where we can talk. *[Reads on:]*
"Hardware targets from the project proposal include up to 30 reservoirs, blends up to
250 mL, per-powder gravimetric accuracy of ±1 mg with a ±0.1 mg stretch goal, and
cross-contamination characterization across five to seven representative L-PBF feedstock
powders."

**02:49 Sterling:** I don't think we need the cross-contamination at all, because we're
not cross-contaminating. We won't mention [it]. We'll just point to [the fact] that we'll
be doing a multi-doser.

**03:04 Sterling:** *[Reads the start of the second paragraph:]* "A central research
thread of the project is evaluating how far agentic AI and generative ('text-to-CAD')
tools can carry mechanical design of a real laboratory instrument. We used GitHub Copilot
coding agents with multiple large language models to generate and revise parametric CAD…"

**03:40 Sterling:** This would probably be a good part to say, like, "between these dates
and using these models". Like, we used [them] between April [and…]. So it also kind of
gives a sense of how quickly the project progressed.

*[Sterling reads the rest of the abstract: the end of the second paragraph, through
"Throughout, the engineers have not opened a traditional CAD graphical interface"; the
third paragraph, from "Several lessons have emerged" (04:39); and the fourth, from "The
poster will present…" to "…aerospace additive manufacturing."]*

**06:25 Sterling:** Nice. How do you feel about taking this as a base?

**Sam:** Yeah. That went through a little bit of iteration, but yeah… with that, it's a
little… yeah.

**06:38 Sterling:** Let's do a couple [of] things. Maybe first… *[Dictates the prompt to
Claude Code:]* "Start with the Utah AI convergence abstract as our new starting point
here. Let's update this to be past tense and make sure this is revised according to any
recent updates, but largely we should keep the same structure and flow of that original
one and not add unnecessary details." *[Aside on dictating: "I forget I actually have to
say 'period'… I do [that] for most of the time." The prompt as sent ends "Show me the new
version".]*

## Part 2: Brainstorming the figures (07:57–28:50)

**07:57 Sterling:** While that's running, let's kind of go back to brainstorming the
figures. We can be a little bit more open on this one; we can just be kind of free-form
here right now. What are the figures and tables that we want to show people, that we
would [trust?]…

**08:24 Sterling:** So, plus the real doser, the assembled one, and, like, an…

**Sam?:** Exploded [view]?

**Sterling:** Exploded.

**08:41 Sam:** Blow it up? We didn't blow it up. We don't want to.

**08:46 Sterling:** Even though they technically could blow up. [We're] putting flammable
[powders in]… sometimes. Yeah. That's the real-doser image. We're kind of having that
correspondence with these. There's some question of whether or not we want to show kind
of what we did in the poster, like [the commercial] comparison systems. I don't know if
it will be OK to include some of those.

**Sam?:** Oh, I see what you're saying. Because, you know, like METTLER TOLEDO and other
stuff.

**09:11 Sam:** Maybe we can['t] take their pictures and stuff, [so] we'll leave it out. I
think it's OK. [?]

**09:14 Sterling:** I think this will be important. Maybe… how do we want to bring the
generative-CAD piece in?

**09:23 Sam:** I think the comparisons between what it brought up and what we did are
helpful.

**Sterling:** Um, maybe we could… well, let's see. Do you have an idea of one of those?

**09:39 Sam:** I have a couple [examples]. Yeah, they're [?] many forms. I think the tap
collar is helpful, maybe. And there's also the version of… there's the different, like,
the assembly we made with, like, CADSmith and Zoo and all those.

**Sterling:** Yeah, that's right. Like, a bunch of different versions.

**Sam:** Yeah. Um, there's the mounting plate, where I kept telling it to do a different
thing, but, like, my description was wrong, because, like, it was… with the gaps in the
mounting plate.

**Sterling:** Yeah.

**Sam:** And we just find something and we just show differences between, like, how we
designed [it and what it made]. And, like, the baseplate and the mounting plate both had,
like, serious problems.

**10:40 Sterling:** So, in terms of the figure, I could imagine something where, if we're
looking at the tap collar, we could sort of call that out, and have… and then we have the
original…

**Sam:** I see.

**Sterling:** …and the human redesign, right? The idea was, when you brought this up, it
was the idea that you redesigned it and made it a little bit better, right?

**Sam:** Yeah. Or a lot better.

**11:39 Sam:** At this point now, it's very different.

**11:42 Sterling:** Yeah, yeah. All of this is in the context of what we've done so far
during the course of the project. Not, like, "what would happen if we did it today?",
right?

**11:49 Sam:** Or, like… because there's a version that's on here right now. It's a
version from months ago.

**Sterling?:** Some edits?

**Sam:** Oh, yeah, that's right. These versions here, like this one: the actual version is
still different than even this one. This one also still has problems. I think we…

**12:13 Sterling:** Do… Oh, no, that's a good point. I think we do want this to be, like,
[the] final version.

**12:23 Sam:** Yeah, I think so. We might do a new real picture, then.

**12:30 Sterling:** Yeah. And that's this issue: is it about the powder doser, or is it
about the generative CAD? It's really splitting across two things. Including the final
version, well, that's definitely about the powder doser, [and] including the version that
we landed on. In some sense, we could also maybe show a timeline.

**Sam:** Yeah.

**13:07 Sterling:** Something… yeah, really just go to the images: characteristic,
representative things, like "here was where we were at by this point, in this month".

**13:25 Sam:** We [could] even have, like… if it's a line, the top could be AI and the
bottom could be engineers.

**Sterling:** Oh, yeah, yeah. That's [it]… where we can see what we're doing and when.

**13:36 Sam:** Which one would be… [?] on top of it, just that one side… [?]

**13:44 Sterling:** Yeah. And that could be, like, key designs, not everything here. And
that might also be a good point to say, OK, [which] agent and [which] model.

**Sam:** Oh, yeah.

**Sterling:** They bring in… yeah, we can have those kind of separate there. But I think
it's so obvious now how important that is. It pains me a little bit (14:11), and it's
like, what if we had a prompt, a three-shot [?] prompt, for a new powder doser? But it's
kind of what we're doing with the multi-doser. There's nothing that can replace the fact
that we've been testing and putting all this design thinking, for nine months, into what
we want this powder doser to be like and to do. No one can change the fact that we used
it in a real workflow.

**15:20 Sterling:** I think this will be good on the generative-CAD side. I think this
schematic figure, that will primarily be helping out with the powder doser: what we
actually did. Maybe… I almost wonder if this one… could we encapsulate [it] in there?
This doesn't necessarily have to be matched up one-to-one. [The] Zoo comparison thing:
do you think that's still worthwhile to include?

**15:53 Sam:** We could just do it in words, if anything. We could just say, like, "we
tried these three things and this one's the best". And we're not using it anymore; we're using
Onshape.

**16:04 Sterling:** I think it might… I don't know, it's almost like a bit of a diss to
CADSmith. I was not impressed at all. And I think that might be worth pointing out: a gap
in the literature. All of these literature studies that [are] published on generative
CAD, versus just using frontier models. I think I might still try to include the CADSmith
one. Again, I think it's an important point to make. And we don't have to say anything
about it: "OK, we did very similar prompts for these three things, and here are the
results."

**16:40 Sam:** Do you think [we] show the images still?

**16:42 Sterling:** Yeah, I think still show the images. That could go in SI, in
Supporting Information. That's actually maybe better.

**16:49 Sam:** I like having it in words in there.

**16:53 Sterling:** And anything in SI should be referenced in the main [text].

**Sam?:** Absolutely.

**Sterling:** So that's where I think that'll work out. The mounting-plate gap…

**17:05 Sam:** I think that's just kind of user error with AI. Not user error, but just
an interesting case.

**Sterling:** I think so too, yeah.

**Sam:** We include it if we need it, but it's not necessary to the… I don't know, it's
kind of fun. It's a good case study, but I don't know if we need to have a case study in
there.

**17:23 Sterling:** I could see us having a discussion section that is kind of trying to
capture that lesson-centred piece. Manual redesign: is that… do you think… Should we
have, like, the v0 and the v1? v0 is sort of the AI-generated piece, and then, OK, we did
a redesign. Would it be worthwhile to show the differences between those things?

**17:56 Sam:** I think you can show that in this timeline. I think those pictures in the
timeline can be both, like, full assemblies of "look what AI made, it doesn't make any
sense", all the way to "look, we both, like, modelled this in this way".

**18:17 Sam:** Let's see what [other] ones we're going to have. Potentially, like, the
three-phase [dosing]? I don't know.

**18:36 Sterling:** Oh, yeah, I think that's worth [it], just showing how we're doing it.

**18:42 Sam:** I think showing the tilts on the auger doesn't really add anything.

**18:47 Sterling:** I think we can show that one of the… sorry, I need to get better at
finishing my sentences. I think it may be worthwhile to take some of the videos that
we've had and ask for keyframes to be pulled out from them, and we can do these kinds of
workflows with keyframes. In terms of that, what are those called? … One of those, I
think, would be…

**19:45 Sam?:** The dosing stages?

**Sterling:** Yeah, I like that. I think another one that we could do is… maybe that's
the main one.

**20:09 Sam:** We could talk about how to load the augers and stuff.

**Sterling:** Oh, yeah.

**Sam:** Or, like, also something like installing and taking them out. We could install
an auger on there.

**20:38 Sterling:** Yeah. If we have any other videos… The only other thing I think of is
assembly stuff.

**20:49 Sam:** Yeah. With some of Will's… I guess this might be the same: with Will's new
modular design for the stand, just adjusting it. Which might [need] another assembly
[guide], but we should make sure of that. Because if we're going to send it out to
people… That is nice, I'm just realizing: if we're going to send it out to a bunch of
people, we can [take] his laser-cut stand [parts] and just cut them out of a giant sheet
of wood.

**21:41 Sterling:** I'm not sure we need to do much more than have something for the
dosing stages.

**21:53 Sam:** It'd be cool to have, like, a real kind of thing along with the feedback
stages: like, have this, and this little feedback block diagram, and this thing. You'd
have a picture for each of those, and see, like, "dose request" going through these.
Yeah, they probably feel like it's all my tapping on just a certain image [?], but yeah.

**22:20 Sterling:** We could kind of [do it in] that same sense: it's like the Claude
ping, or "doser, dose X amount".

**Sam:** Yeah.

**22:36 Sam:** And you said that could be, like, you know, how we can have the Claude ping
there and then have it with, like, an image of it. Are you saying, like…

**22:51 Sterling:** So, I have some videos of me on my phone, like a screen recording on
my phone. It's like "@claude…", I'll say. Or you could grab a snapshot from GitHub.

**Sam:** Yeah, awesome. Yeah, that's great.

**23:05 Sterling:** Which then gets us into results and data.

**23:09 Sam:** I think somewhere a picture of, like, powder actually in the [beakers?],
like, actually on the scale, is nice.

**23:20 Sterling:** Yeah, I [see] what you mean. If we wanted a little bit of visual
effect: grab all the dosers that we currently have and line them up, and then we just
make little callouts of, like, what's inside each one.

**23:37 Sam:** That's great. The only other picture in here that I think [matters],
like, tables and figures and good graphs aside, is this one, which is my drawing
of this, and then this. *[Probably Fig. 6: Sam's hand sketch of the multi-doser carriage
and his Onshape model of it.]* But this is my drawing and my CAD model; like, I modelled
this. To me this says, like, "this is the drawing you gave me, and this is what CAD…
what AI thought". I don't actually [like?] that very much. But we could potentially have,
like, a drawing that I gave it, and then [what it made].

**24:27 Sterling:** Yeah, I think that could be worthwhile.

**24:30 Sam:** Or it could be in the timeline. Like, on the bottom we'd have drawings as
well as [the models].

**24:45 Sam:** Yeah, I like that. I like the callouts too. I think you can have, like, one
big image, like one big figure that's [the doser] here or something like that, whatever
we have, with a bunch of callouts. Like, have this in a callout, and everything. I think
that would be really cool.

**25:13 Sterling:** Yeah, that's really great.

**25:27 Sterling:** *[Writing the list.]* Green is main manuscript, blue is SI. So,
Figure 1…

**Sam:** Yeah.

**Sterling:** …that includes in it all of the callouts and stuff. Figure 2?

**Sam:** Yeah.

**Sterling:** That might… Figure 3? Dosing stages?

**26:12 Sam:** It just depends on how we end up structuring the paper itself.

**26:17 Sterling:** Yeah. But should we say this is definitely [in] the main? And some of
these might be [SI]…

**26:32 Sam:** And maybe the instructions can be in [the] SI, and, like, the swapping can
be main. Like, adjusting the height, the assembly, can be SI. Yeah:
basic usage can be in the figure[s], but background usage can be SI or something. I
think [the Claude] ping as well can be in [a] figure, maybe. Sorry: the Claude ping can
be in the main, just because that's the main way that we [use] it.

**27:16 Sterling:** Dosers lined up: I think that one we could either have it…

**27:29 Sam:** I think that one's mainly shock value, where it's, like, cool: we say that
we dose 13, but we don't [get] to see them. I think it should be in the main.

**Sterling:** OK, sounds good. Yeah, that's the other one. And this could maybe be… it
might be one that we try to make an inset, or we just keep it as, like, a very small…

**27:48 Sam:** …side figure. It could even be a [colour? collar?] on the auger, or
something, on the main one. Um, if it's in the
main, it should be green.

**Sterling:** Thank you. And then the Zoo comparisons… Let's go to 1, 2…

**28:28 Sterling:** …[Figs.] 1, 2 and 3, [the] other figures in the main
manuscript. And then let's get into… make one of those in the results, like the dosing
[results].

## Part 3: The current results figures (28:52–33:02)

*[They look at Figs. 3–5 of the current draft.]*

**28:52 Sterling:** How do you feel about these three figures?

**29:09 Sam:** I like this one. OK, so, um…

**29:13 Sterling:** I think this one… I think it's helpful. It's OK.

**29:26 Sam?:** Yeah, I think it's not… Like, these two are pretty similar, but I think
it's OK to have both. *[Probably Figs. 3a and 4a, which both show mass per revolution.]*

**29:41 Sterling:** Um, I think this one… is there really a need to separate out slow
versus [fast]?

**29:49 Sam:** And this is a variation between revolutions, but I don't know…

*[Fig. 3c: mass per revolution against the variation between revolutions, shaded in two
groups.]*

**Sterling:** Oh, that's right.

**Sam:** I'm not sure how helpful that is.

**30:15 Sterling:** I feel like this…

**30:20 Sam:** …is, like, these are the slow ones. And so, unless we're, like… yeah, we
say we're not going to look at these, and then we look at [the] description, like the
differences between these… It's not super helpful just to say, like, yeah, three of them
are slow, over and over again. *[In Fig. 4a the seven free-flowing powders overlap and
are bracketed, so only the three slow powders stand apart.]*

**30:32 Sterling:** Yeah. I think 4a is better as a table anyway. And maybe SI.

**30:46 Sterling:** *[Reading the Fig. 4b caption:]* "Mass released by one solenoid tap…
against mass per auger revolution."

**30:49 Sam:** This is in here: "for the six powders whose tap increment exceeded twice
its standard error". So it's not even all the powders. I like having something for the
tap there.

**30:59 Sterling:** Yeah, I think so. It's like there's three mechanisms for [dosing?] it,
and they have interplay with each other.

**31:06 Sam:** I like having something on there. I don't love that it's just these six. I
think you could just put all of them on there.

**Sterling:** Yeah, that is kind of… You know what? I'm not sure. Just like who's… Yeah.
Let me think about it. So 4b is all [of them]…

**31:26 Sam:** Or something, yeah. And this could also just be, like, a bar graph of, like,
mass per solenoid tap.

**Sterling:** Yeah.

**31:39 Sam:** I like having some kind of error [bar].

**31:49 Sterling:** Yeah, I think that is useful. I think [it's a] small thing. And yeah,
this was our whole 50, 200, 1 gram, with repeats. And what's this one, (d)?

**32:07 Sam:** This is time to finish the dose. I don't know. I like these. This one, I
feel, is not necessarily…

**32:20 Sterling:** And also, it doesn't make sense to put this [here]. It implies that
there's some connection to the y-axis here, when there is none.

**32:31 Sam:** Yeah. So it's already bad if we can't tell that. But here it's like, I
don't know what this… I don't know what all these boxes are.

**Sterling?:** Yeah, I guess the times to complete for each of these things.

**Sam:** Yeah, but if it's not… I think, per… yeah, it doesn't… like, drop it. Or I think
the time isn't really what we're looking for anyway. Like, we can mention it somewhere in
there, but it doesn't have to be a major part of this.

**33:02 Sam:** That's… that's it.

## Part 4: Next steps (33:07–34:31)

**33:08 Sterling:** OK, you said five minutes.

**33:10 Sam:** Yeah, I gotta go now. So is it writing a new one right now?

**Sterling:** It did write a new abstract.

**Sam:** OK. It wrote a new abstract, or did it write a new figure?

**33:18 Sterling:** I haven't [prompted] it for that yet. I think I'll have it start with
just trying to make all of these, and then we can review and see if the figures look how
we want them. And then we'll have it kind of build the paper on that, if that sounds
[good].

**Sam?:** So it's [starting] over? [?]

**33:32 Sterling?:** Yeah, I think so. I think we have more kind of [?] than we do.

**33:36 Sterling:** And we can always point it back and say, "yeah, it's this thing". But
I think it's maybe a little bit too locked into its own version, because it's iterated so
much on it. Yeah, models get… yeah, some… you know, some [?] lost.

**Sam:** Yes. I promise I'll be better at editing those.

**Sterling:** OK. Let me know.

**34:02 Sam:** It's done.

**34:05 Sterling:** I'm going to have it go from everything here, probably back to… maybe a
new PR.

**34:12 Sam:** I'll [write] these down. And then once we get the [manuscript] from there,
I'll edit it as well.

**Sterling:** Perfect. Thank you.

*[The recording ends at 34:31.]*

---

## Glossary of corrected mishearings

| Raw Whisper output | Corrected |
|---|---|
| outlet discovery | alloy discovery |
| designed with generative algorithms and intelligence | designed with generative artificial intelligence |
| an open source powder coaster this research cat pcb | an Open-Source Powder Doser for L-PBF Feedstock Research: CAD, PCB |
| out of manufacturing | additive manufacturing |
| self-drying | self-driving |
| laser powder with fusion | laser powder bed fusion |
| plus or minus 0.1 milligrams threshold | ±0.1 mg stretch goal |
| 5 to 7 percent of laser powder diffusion feedstock values | five to seven representative L-PBF feedstock powders |
| ancient AI | agentic AI |
| host-to-generative CAD services | hosted generative-CAD services |
| The cluster will present | The poster will present |
| cap collar | tap collar |
| billet materials | bill of materials |
| GenithCAD, Genufacada, genre of CAD | generative CAD |
| a couple eggs | a couple [examples] |
| cad smith, CadSmith | CADSmith |
| melding plate cap | mounting-plate gap |
| main screen | main [text] |
| clawed ping, cloud page | Claude ping |
| plug things | [the Claude] ping |
| insect | inset |
| master solenoid tab | mass per solenoid tap |
| the manager (34:12) | the [manuscript] |
| Mettler-Tolite (second pass) | METTLER TOLEDO |
| in the desert, in the blizzards (23:12) | in the [beakers?] |
| problems (16:36; second pass: prompts) | prompts |
| exaggerated (33:39; second pass: iterated) | iterated |
