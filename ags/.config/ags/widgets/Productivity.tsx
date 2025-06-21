// AGS v2 Productivity Tools Widget

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"
import Gtk from "gi://Gtk?version=3.0"

interface Task {
    id: number
    text: string
    completed: boolean
    createdAt: Date
}

interface ClipboardItem {
    id: number
    text: string
    timestamp: Date
}

const tasks = Variable<Task[]>([])
const clipboardHistory = Variable<ClipboardItem[]>([])
const currentNote = Variable("")
const timerSeconds = Variable(0)
const timerRunning = Variable(false)
const pomodoroMinutes = Variable(25)
const breakMinutes = Variable(5)
const isBreak = Variable(false)

// Timer logic
let timerInterval: any = null

function startTimer() {
    if (timerInterval) clearInterval(timerInterval)
    timerRunning.set(true)
    timerInterval = setInterval(() => {
        const current = timerSeconds.get()
        if (current > 0) {
            timerSeconds.set(current - 1)
        } else {
            timerRunning.set(false)
            clearInterval(timerInterval)
            // Toggle between work and break
            if (isBreak.get()) {
                isBreak.set(false)
                timerSeconds.set(pomodoroMinutes.get() * 60)
                execAsync(["notify-send", "Pomodoro", "Break finished! Time to work."])
            } else {
                isBreak.set(true)
                timerSeconds.set(breakMinutes.get() * 60)
                execAsync(["notify-send", "Pomodoro", "Work session finished! Time for a break."])
            }
        }
    }, 1000)
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval)
    timerRunning.set(false)
}

// Initialize with work time
timerSeconds.set(pomodoroMinutes.get() * 60)

// Poll clipboard
clipboardHistory.poll(5000, async () => {
    try {
        const clip = await execAsync(["wl-paste"]).then(out => out.trim())
        const history = clipboardHistory.get()
        if (clip && !history.some(item => item.text === clip)) {
            return [{
                id: Date.now(),
                text: clip,
                timestamp: new Date()
            }, ...history.slice(0, 9)]
        }
        return history
    } catch {
        return clipboardHistory.get()
    }
})

export default function ProductivityWidget({ fullView = false }: { fullView?: boolean }) {
    // Cleanup interval on widget destroy
    if (typeof globalThis !== "undefined" && globalThis.connect) {
        globalThis.connect("destroy", () => {
            if (timerInterval) clearInterval(timerInterval)
        })
    }
    if (fullView) {
        return <box className="productivity-full" vertical spacing={12}>
            <label className="widget-title" label="📋 Productivity Tools" />
            
            {/* Tasks Section */}
            <box className="tasks-section" vertical spacing={8}>
                <label className="section-label" label="Tasks" />
                <scrollable heightRequest={150}>
                    <box vertical spacing={4}>
                        {bind(tasks).as(taskList => 
                            taskList.map(task => (
                                <box key={task.id} className="task-item" spacing={8}>
                                    <checkbox active={task.completed}
                                        onActivate={({ active }) => {
                                            const updated = tasks.get().map(t => 
                                                t.id === task.id ? { ...t, completed: active } : t
                                            )
                                            tasks.set(updated)
                                        }} />
                                    <label label={task.text} 
                                        className={task.completed ? "task-completed" : ""}
                                        hexpand />
                                    <button className="delete-button"
                                        onClicked={() => {
                                            tasks.set(tasks.get().filter(t => t.id !== task.id))
                                        }}>
                                        <icon icon="user-trash-symbolic" />
                                    </button>
                                </box>
                            ))
                        )}
                    </box>
                </scrollable>
                <entry className="task-input"
                    placeholderText="Add new task..."
                    onActivate={(self) => {
                        if (self.text) {
                            tasks.set([...tasks.get(), {
                                id: Date.now(),
                                text: self.text,
                                completed: false,
                                createdAt: new Date()
                            }])
                            self.text = ""
                        }
                    }} />
            </box>

            {/* Pomodoro Timer */}
            <box className="pomodoro-section" vertical spacing={8}>
                <label className="section-label" label={bind(isBreak).as(b => b ? "Break Time" : "Pomodoro Timer")} />
                <label className="timer-display" 
                    label={bind(timerSeconds).as(s => {
                        const mins = Math.floor(s / 60)
                        const secs = s % 60
                        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
                    })} />
                <box spacing={6}>
                    <button className="timer-button"
                        onClicked={() => timerRunning.get() ? stopTimer() : startTimer()}>
                        {bind(timerRunning).as(r => r ? "Pause" : "Start")}
                    </button>
                    <button className="timer-button"
                        onClicked={() => {
                            stopTimer()
                            isBreak.set(false)
                            timerSeconds.set(pomodoroMinutes.get() * 60)
                        }}>
                        Reset
                    </button>
                </box>
            </box>

            {/* Clipboard History */}
            <box className="clipboard-section" vertical spacing={8}>
                <label className="section-label" label="Clipboard History" />
                <scrollable heightRequest={100}>
                    <box vertical spacing={4}>
                        {bind(clipboardHistory).as(history => 
                            history.map(item => (
                                <button key={item.id} className="clipboard-item"
                                    onClicked={() => execAsync(["wl-copy", item.text])}>
                                    <label label={item.text.slice(0, 50) + (item.text.length > 50 ? "..." : "")} />
                                </button>
                            ))
                        )}
                    </box>
                </scrollable>
            </box>

            {/* Quick Note */}
            <box className="notes-section" vertical spacing={8}>
                <label className="section-label" label="Quick Note" />
                <entry className="note-input"
                    text={bind(currentNote)}
                    placeholderText="Type your note here..."
                    onChanged={(self) => currentNote.set(self.text)} />
                <button className="save-note-button"
                    onClicked={() => {
                        if (currentNote.get()) {
                            const note = currentNote.get()
                            const date = new Date().toISOString()
                            execAsync(["bash", "-c", `echo "${date}: ${note}" >> ~/notes.txt`])
                            currentNote.set("")
                            execAsync(["notify-send", "Note Saved", "Note saved to ~/notes.txt"])
                        }
                    }}>
                    Save Note
                </button>
            </box>
        </box>
    }

    return <box className="productivity-compact">
        <icon icon="view-list-symbolic" />
    </box>
}