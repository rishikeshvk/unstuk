package com.rishikeshvk.unstuk.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.flow.ComplaintFlow
import com.rishikeshvk.unstuk.flow.FixStep
import com.rishikeshvk.unstuk.flow.Reply
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Where the conversation is. One screen at a time: that is the whole navigation model. */
sealed interface Screen {
    data object Home : Screen

    data class Topic(val area: Area) : Screen

    /** A fix is running; back is blocked so a half-run fix never loses its result. */
    data class Working(val fix: FixEntry) : Screen

    data class Answer(val reply: Reply) : Screen

    /** The intent's own tips, after "Still not working?". */
    data class Tips(val intent: IntentEntry) : Screen

    data object Access : Screen

    data object Debug : Screen
}

/**
 * [complaint] is kept so a "didn't catch that" reply can show the words back; [fixed] holds the fixes verified
 * in this conversation, so a later scan can mark them; [howFixed] is the last run's ladder.
 */
data class HelpState(
    val screen: Screen = Screen.Home,
    val complaint: String = "",
    val fixed: Set<String> = emptySet(),
    val howFixed: List<FixStep> = emptyList(),
    val bannerDismissed: Boolean = false
)

private data class RunRequest(val intentId: String, val fix: FixEntry, val confidence: Double)

/**
 * Owns one help conversation and survives configuration changes: the text-size fix, a theme switch or a rotation
 * recreates the Activity mid-run, and the run and its reply must outlive it.
 */
class HelpViewModel(app: Application) : AndroidViewModel(app) {
    private val flow = ComplaintFlow(app)
    private val catalog = CatalogLoader.load(app.assets)
    private var trialId = newTrialId()
    private var lastRun: RunRequest? = null
    private var job: Job? = null

    var state by mutableStateOf(HelpState())
        private set

    fun intentsIn(area: Area): List<IntentEntry> = catalog.intents.filter { it.area == area }

    fun updateComplaint(text: String) {
        state = state.copy(complaint = text)
    }

    fun submit() {
        val complaint = state.complaint.trim()
        if (complaint.isEmpty()) return
        respond { flow.start(complaint, trialId) }
    }

    fun openTopic(area: Area) = go(Screen.Topic(area))

    /** The user named the issue themselves: from a topic, or from a clarifying question. */
    fun pick(intentId: String) = respond { flow.choose(intentId, trialId) }

    fun noneOfThese() = go(Screen.Answer(Reply.Decline))

    fun confirm(intentId: String, fix: FixEntry, confidence: Double) =
        run(RunRequest(intentId, fix, confidence))

    fun retry() {
        lastRun?.let(::run)
    }

    fun recheck(guide: Reply.Guide) =
        respond { flow.recheck(guide.intent.id, guide.fix.id, lastRun?.confidence ?: 1.0, trialId) }

    fun showTips(intent: IntentEntry) = go(Screen.Tips(intent))

    /** A reply the screen already holds, such as a guide offered as the next step after a fix. */
    fun showReply(reply: Reply) = go(Screen.Answer(reply))

    fun openAccess() = go(Screen.Access)

    fun openDebug() = go(Screen.Debug)

    fun dismissBanner() {
        state = state.copy(bannerDismissed = true)
    }

    /** System back: one level up. Returns false when there is nowhere to go, so the app closes. */
    fun back(): Boolean = when (state.screen) {
        Screen.Home -> false
        is Screen.Working -> true
        Screen.Debug -> true.also { go(Screen.Access) }
        else -> true.also { go(Screen.Home) }
    }

    /** "Done" and "Start over": a new conversation with a clean slate. */
    fun finish() {
        trialId = newTrialId()
        lastRun = null
        state = HelpState(bannerDismissed = state.bannerDismissed)
    }

    private fun go(screen: Screen) {
        if (state.screen is Screen.Working) return
        state = state.copy(screen = screen)
    }

    private fun respond(next: suspend () -> Reply) {
        if (job?.isActive == true) return
        job = viewModelScope.launch {
            val reply = withContext(Dispatchers.Default) { next() }
            if (reply is Reply.Run) {
                runNow(RunRequest(reply.intent.id, reply.fix, reply.confidence))
            } else {
                show(reply)
            }
        }
    }

    private fun run(request: RunRequest) {
        if (job?.isActive == true) return
        job = viewModelScope.launch { runNow(request) }
    }

    private suspend fun runNow(request: RunRequest) {
        lastRun = request
        state = state.copy(screen = Screen.Working(request.fix))
        val reply = withContext(Dispatchers.Default) {
            flow.run(request.intentId, request.fix.id, request.confidence, trialId)
        }
        // Only a run's own success has a ladder to show; after a recheck the user made the change.
        val steps = if (reply is Reply.Fixed) {
            withContext(Dispatchers.IO) { flow.howFixed(trialId) }
        } else {
            emptyList()
        }
        show(reply, steps)
    }

    private fun show(reply: Reply, howFixed: List<FixStep> = emptyList()) {
        val fixed = if (reply is Reply.Fixed) state.fixed + reply.fix.id else state.fixed
        state = state.copy(screen = Screen.Answer(reply), fixed = fixed, howFixed = howFixed)
    }

    private fun newTrialId() = "ui-${System.currentTimeMillis()}"
}
