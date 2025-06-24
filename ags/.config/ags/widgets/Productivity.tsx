// ags/.config/ags/widgets/Productivity.tsx

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

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
    if (typeof globalThis !== "undefined" && globalThis.connect) {
        globalThis.connect("destroy", () => {
            if (timerInterval) clearInterval(timerInterval)
        })
    }

    if (fullView) {
        return new Widget.Box({
            className: "productivity-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "📋 Productivity Tools"
                }),
                
                // Tasks Section
                new Widget.Box({
                    className: "tasks-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Tasks"
                        }),
                        // @ts-ignore - Scrollable widget
                        new Widget.Scrollable({
                            heightRequest: 150,
                            child: new Widget.Box({
                                vertical: true,
                                spacing: 4,
                                children: bind(tasks).as(taskList => 
                                    taskList.map(task => new Widget.Box({
                                        className: "task-item",
                                        spacing: 8,
                                        children: [
                                            // @ts-ignore - CheckBox widget
                                            new Widget.CheckBox({
                                                active: task.completed,
                                                onActivate: ({ active }: any) => {
                                                    const updated = tasks.get().map(t => 
                                                        t.id === task.id ? { ...t, completed: active } : t
                                                    )
                                                    tasks.set(updated)
                                                }
                                            }),
                                            new Widget.Label({
                                                label: task.text,
                                                className: task.completed ? "task-completed" : "",
                                                hexpand: true
                                            }),
                                            new Widget.Button({
                                                className: "delete-button",
                                                onClicked: () => {
                                                    tasks.set(tasks.get().filter(t => t.id !== task.id))
                                                },
                                                child: new Widget.Icon({ icon: "user-trash-symbolic" })
                                            })
                                        ]
                                    }))
                                )
                            })
                        }),
                        new Widget.Entry({
                            className: "task-input",
                            placeholderText: "Add new task...",
                            onActivate: (self: any) => {
                                if (self.text) {
                                    tasks.set([...tasks.get(), {
                                        id: Date.now(),
                                        text: self.text,
                                        completed: false,
                                        createdAt: new Date()
                                    }])
                                    self.text = ""
                                }
                            }
                        })
                    ]
                }),

                // Pomodoro Timer
                new Widget.Box({
                    className: "pomodoro-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: bind(isBreak).as(b => b ? "Break Time" : "Pomodoro Timer")
                        }),
                        new Widget.Label({
                            className: "timer-display",
                            label: bind(timerSeconds).as(s => {
                                const mins = Math.floor(s / 60)
                                const secs = s % 60
                                return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
                            })
                        }),
                        new Widget.Box({
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: "timer-button",
                                    label: bind(timerRunning).as(r => r ? "Pause" : "Start"),
                                    onClicked: () => timerRunning.get() ? stopTimer() : startTimer()
                                }),
                                new Widget.Button({
                                    className: "timer-button",
                                    label: "Reset",
                                    onClicked: () => {
                                        stopTimer()
                                        isBreak.set(false)
                                        timerSeconds.set(pomodoroMinutes.get() * 60)
                                    }
                                })
                            ]
                        })
                    ]
                }),

                // Clipboard History
                new Widget.Box({
                    className: "clipboard-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Clipboard History"
                        }),
                        // @ts-ignore - Scrollable widget
                        new Widget.Scrollable({
                            heightRequest: 100,
                            child: new Widget.Box({
                                vertical: true,
                                spacing: 4,
                                children: bind(clipboardHistory).as(history => 
                                    history.map(item => new Widget.Button({
                                        className: "clipboard-item",
                                        onClicked: () => execAsync(["wl-copy", item.text]),
                                        child: new Widget.Label({
                                            label: item.text.slice(0, 50) + (item.text.length > 50 ? "..." : "")
                                        })
                                    }))
                                )
                            })
                        })
                    ]
                }),

                // Quick Note
                new Widget.Box({
                    className: "notes-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Quick Note"
                        }),
                        new Widget.Entry({
                            className: "note-input",
                            text: bind(currentNote),
                            placeholderText: "Type your note here...",
                            onChanged: (self: any) => currentNote.set(self.text)
                        }),
                        new Widget.Button({
                            className: "save-note-button",
                            label: "Save Note",
                            onClicked: () => {
                                if (currentNote.get()) {
                                    const note = currentNote.get()
                                    const date = new Date().toISOString()
                                    execAsync(["bash", "-c", `echo "${date}: ${note}" >> ~/notes.txt`])
                                    currentNote.set("")
                                    execAsync(["notify-send", "Note Saved", "Note saved to ~/notes.txt"])
                                }
                            }
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "productivity-compact",
        children: [new Widget.Icon({ icon: "view-list-symbolic" })]
    })
}
