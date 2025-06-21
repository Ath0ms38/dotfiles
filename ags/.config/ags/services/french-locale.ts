// ags/.config/ags/services/french-locale.ts
// Provides French localization utilities for AGS widgets

export const frenchLocale = {
    daysShort: ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'],
    daysLong: [
        'Dimanche', 'Lundi', 'Mardi', 'Mercredi',
        'Jeudi', 'Vendredi', 'Samedi'
    ],
    monthsShort: [
        'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
        'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'
    ],
    monthsLong: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ],
    formatDate: (date: Date) => {
        // e.g. "Vendredi 21 Juin 2025"
        const day = frenchLocale.daysLong[date.getDay()];
        const d = date.getDate();
        const month = frenchLocale.monthsLong[date.getMonth()];
        const year = date.getFullYear();
        return `${day} ${d} ${month} ${year}`;
    },
    formatTime: (date: Date) => {
        // e.g. "15:47"
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    },
    formatDay: (date: Date) => {
        // e.g. "21"
        return date.getDate().toString();
    },
    firstDayOfWeek: 1, // Monday
};