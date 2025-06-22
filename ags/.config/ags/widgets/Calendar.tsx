// AGS v2 Calendar Widget with French Localization - Anime Room Theme

import { Variable, bind } from "astal"
import { frenchLocale } from "../services/french-locale"
import { execAsync } from "astal/process"
import Gtk from "gi://Gtk?version=3.0"

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
        return <box className="calendar-widget-full" vertical spacing={16}>
            <label className="widget-title" label="📅 Calendrier" />
            
            {/* Main date/time display */}
            <box className="date-time-section" vertical spacing={12}>
                <label className="french-time"
                    label={bind(currentDate).as(formatFrenchTime)} />
                    
                <label className="french-date"
                    label={bind(currentDate).as(formatFrenchDate)} />
                
                <label className="week-number"
                    label={bind(currentDate).as(date => `📆 Semaine ${getWeekNumber(date)}`)} />
            </box>
            
            {/* Date statistics */}
            <box className="date-info" vertical spacing={8}>
                <box className="info-row" spacing={8}>
                    <label label="Jour de l'année:" />
                    <box hexpand />
                    <label label={bind(currentDate).as(date => {
                        const start = new Date(date.getFullYear(), 0, 0)
                        const diff = date.getTime() - start.getTime()
                        const oneDay = 1000 * 60 * 60 * 24
                        const dayNum = Math.floor(diff / oneDay)
                        return `${dayNum} / 365`
                    })} />
                </box>
                
                <box className="info-row" spacing={8}>
                    <label label="Jours restants:" />
                    <box hexpand />
                    <label label={bind(currentDate).as(date => {
                        const endYear = new Date(date.getFullYear(), 11, 31)
                        const diff = endYear.getTime() - date.getTime()
                        const oneDay = 1000 * 60 * 60 * 24
                        const days = Math.ceil(diff / oneDay)
                        return `${days} jours`
                    })} />
                </box>
                
                <box className="info-row" spacing={8}>
                    <label label="Progression:" />
                    <box hexpand />
                    <label label={bind(currentDate).as(date => {
                        const start = new Date(date.getFullYear(), 0, 1)
                        const end = new Date(date.getFullYear(), 11, 31)
                        const total = end.getTime() - start.getTime()
                        const current = date.getTime() - start.getTime()
                        const percent = Math.round((current / total) * 100)
                        return `${percent}%`
                    })} />
                </box>
            </box>

            {/* Quick actions */}
            <box className="calendar-actions" spacing={8}>
                <button className="action-button" 
                    onClicked={() => execAsync(["gnome-calendar"]).catch(() => 
                        execAsync(["firefox", "--new-window", "https://calendar.google.com"])
                    )}>
                    📅 Calendrier
                </button>
                <button className="action-button" 
                    onClicked={() => execAsync(["firefox", "--new-window", "https://calendar.google.com"])}>
                    🌐 Google Calendar
                </button>
            </box>
        </box>
    }

    // Compact view (not used in popup)
    return <box className="calendar-widget-compact">
        <icon icon="x-office-calendar-symbolic" />
    </box>
}
