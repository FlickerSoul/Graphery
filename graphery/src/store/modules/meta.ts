export default {
  namespaced: true,
  state: {
    siteName: 'Graphery',
    navigationButtons: [
      { name: 'Home', icon: 'mdi-home-circle' },
      { name: 'Tutorials', icon: 'mdi-newspaper-variant' },
      { name: 'Graphs', icon: 'mdi-graph' },
      { name: 'About', icon: 'mdi-clipboard-account-outline' },
      { name: 'Account', icon: 'mdi-account-circle' },
      { name: 'Settings', icon: 'mdi-cog' },
    ],
    siteLogo: require('@/assets/images/reed-compbio-logo.png'),
    footerHTML:
      '<div> 2020 © Graphery </div> <div> Built With ❤ By <a href="https://vuejs.org" alt="VUE" target="_blank">Vue</a></div>',
  },
};
