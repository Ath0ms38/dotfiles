// AGS v2 Calendar Widget with French Localization - Fixed with Widget constructors

import { Variable, bind } from "astal"
import { frenchLocale } from "../services/french-locale"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

const currentDate = Variable(new Date()).poll(1000, () => new Date())

function formatFrenchDate(date: Date): string {
    const day = date.getDate()
    const month = frenchLocale.monthsLong[date.getMonth()]
    const year = date.getFullYear()
    const dayName = frenchLocale.daysLong[date.getDay()]
    
    return `${dayName}, ${day} ${month} ${year}`
}

function formatFrenchTime(date: Date): string {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
}

function getWeekNumber(date: Date): number {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
    const dayNum = d.getUTCDay() || 7
    d.setUTCDate(d.getUTCDate() + 4 - dayNum)
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
}

export default function CalendarWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return new Widget.Box({
            className: "calendar-widget-full",
            vertical: true,
            spacing: 16,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "📅 Calendrier"
                }),
                
                // Main date/time display
                new Widget.Box({
                    className: "date-time-section",
                    vertical: true,
                    spacing: 12,
                    children: [
                        new Widget.Label({
                            className: "french-time",
                            label: bind(currentDate).as(formatFrenchTime)
                        }),
                        
                        new Widget.Label({
                            className: "french-date",
                            label: bind(currentDate).as(formatFrenchDate)
                        }),
                        
                        new Widget.Label({
                            className: "week-number",
                            label: bind(currentDate).as(date => `📆 Semaine ${getWeekNumber(date)}`)
                        })
                    ]
                }),
                
                // Date statistics
                new Widget.Box({
                    className: "date-info",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Box({
                            className: "info-row",
                            spacing: 8,
                            children: [
                                new Widget.Label({
                                    label: "Jour de l'année:"
                                }),
                                new Widget.Box({ hexpand: true }),
                                new Widget.Label({
                                    label: bind(currentDate).as(date => {
                                        const start = new Date(date.getFullYear(), 0, 0)
                                        const diff = date.getTime() - start.getTime()
                                        const oneDay = 1000 * 60 * 60 * 24
                                        const dayNum = Math.floor(diff / oneDay)
                                        return `${dayNum} / 365`
                                    })
                                })
                            ]
                        }),
                        
                        new Widget.Box({
                            className: "info-row",
                            spacing: 8,
                            children: [
                                new Widget.Label({
                                    label: "Jours restants:"
                                }),
                                new Widget.Box({ hexpand: true }),
                                new Widget.Label({
                                    label: bind(currentDate).as(date => {
                                        const endYear = new Date(date.getFullYear(), 11, 31)
                                        const diff = endYear.getTime() - date.getTime()
                                        const oneDay = 1000 * 60 * 60 * 24
                                        const days = Math.ceil(diff / oneDay)
                                        return `${days} jours`
                                    })
                                })
                            ]
                        }),
                        
                        new Widget.Box({
                            className: "info-row",
                            spacing: 8,
                            children: [
                                new Widget.Label({
                                    label: "Progression:"
                                }),
                                new Widget.Box({ hexpand: true }),
                                new Widget.Label({
                                    label: bind(currentDate).as(date => {
                                        const start = new Date(date.getFullYear(), 0, 1)
                                        const end = new Date(date.getFullYear(), 11, 31)
                                        const total = end.getTime() - start.getTime()
                                        const current = date.getTime() - start.getTime()
                                        const percent = Math.round((current / total) * 100)
                                        return `${percent}%`
                                    })
                                })
                            ]
                        })
                    ]
                }),

                // Quick actions
                new Widget.Box({
                    className: "calendar-actions",
                    spacing: 8,
                    children: [
                        new Widget.Button({
                            className: "action-button",
                            label: "📅 Calendrier",
                            onClicked: () => {
                                execAsync(["gnome-calendar"]).catch(() => 
                                    execAsync(["firefox", "--new-window", "https://calendar.google.com"])
                                )
                            }
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "🌐 Google Calendar",
                            onClicked: () => {
                                execAsync(["firefox", "--new-window", "https://calendar.google.com"])
                            }
                        })
                    ]
                })
            ]
        })
    }

    // Compact view (not used in popup)
    return new Widget.Box({
        className: "calendar-widget-compact",
        children: [
            new Widget.Icon({
                icon: "x-office-calendar-symbolic"
            })
        ]
    })
}