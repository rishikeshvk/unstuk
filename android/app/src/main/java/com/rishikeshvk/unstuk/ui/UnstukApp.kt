package com.rishikeshvk.unstuk.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.ContentTransform
import androidx.compose.animation.SharedTransitionLayout
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import com.rishikeshvk.unstuk.ui.reply.ReplyActions
import com.rishikeshvk.unstuk.ui.reply.ReplyScreen
import com.rishikeshvk.unstuk.ui.reply.TipsReply
import com.rishikeshvk.unstuk.ui.reply.WorkingReply

private const val AREA_KEY = "area-"

/**
 * The whole app: one screen at a time, chosen by the view model's state. A topic tile grows into the topic
 * screen's header (a shared-bounds transform); every other change slides in gently. [debugScreen] exists only
 * in debug builds.
 */
@Composable
fun UnstukApp(vm: HelpViewModel, debugScreen: (@Composable () -> Unit)?) {
    val state = vm.state
    val access = rememberAccessStatus()
    BackHandler(enabled = state.screen != Screen.Home) { vm.back() }
    val actions = remember(vm) { replyActions(vm) }
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        SharedTransitionLayout {
            AnimatedContent(
                targetState = state.screen,
                transitionSpec = { slideFor(targetState) },
                label = "screen"
            ) { screen ->
                Box(Modifier.safeDrawingPadding()) {
                    when (screen) {
                        Screen.Home -> HomeScreen(
                            complaint = state.complaint,
                            onComplaintChange = vm::updateComplaint,
                            onSubmit = vm::submit,
                            onTopic = vm::openTopic,
                            onAccess = vm::openAccess,
                            showBanner = !access.complete && !state.bannerDismissed,
                            accessMissing = !access.complete,
                            onDismissBanner = vm::dismissBanner,
                            tileModifier = { area ->
                                Modifier.sharedBounds(
                                    rememberSharedContentState(AREA_KEY + area.name),
                                    this@AnimatedContent
                                )
                            }
                        )
                        is Screen.Topic -> TopicScreen(
                            area = screen.area,
                            intents = vm.intentsIn(screen.area),
                            onPick = vm::pick,
                            onBack = { vm.back() },
                            modifier = Modifier.sharedBounds(
                                rememberSharedContentState(AREA_KEY + screen.area.name),
                                this@AnimatedContent
                            )
                        )
                        is Screen.Working -> WorkingReply(screen.fix)
                        is Screen.Answer ->
                            ReplyScreen(
                                screen.reply,
                                state.complaint,
                                state.fixed,
                                state.howFixed,
                                actions
                            )
                        is Screen.Tips -> TipsReply(
                            screen.intent,
                            scan = null,
                            state.fixed,
                            actions
                        )
                        Screen.Access -> AccessScreen(
                            status = access,
                            onBack = { vm.back() },
                            onDebug = debugScreen?.let { { vm.openDebug() } }
                        )
                        Screen.Debug -> debugScreen?.invoke()
                    }
                }
            }
        }
    }
}

// Forward into a conversation, back out to Home.
private fun AnimatedContentTransitionScope<Screen>.slideFor(target: Screen): ContentTransform {
    val direction = if (target == Screen.Home) -1 else 1
    return (fadeIn() + slideInHorizontally { direction * it / 8 }) togetherWith fadeOut()
}

private fun replyActions(vm: HelpViewModel) = ReplyActions(
    back = { vm.back() },
    finish = vm::finish,
    updateComplaint = vm::updateComplaint,
    submit = vm::submit,
    openTopic = vm::openTopic,
    pick = vm::pick,
    noneOfThese = vm::noneOfThese,
    confirm = vm::confirm,
    retry = vm::retry,
    recheck = vm::recheck,
    showTips = vm::showTips,
    showReply = vm::showReply
)
