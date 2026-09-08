import { Component, computed, input } from '@angular/core';
import { DiagramGraph, layoutGrafo } from '../grafo-layout';

@Component({
  selector: 'app-grafo-diagrama',
  templateUrl: './grafo-diagrama.html',
  styleUrl: './grafo-diagrama.css',
})
export class GrafoDiagramaComponent {
  readonly grafo = input<DiagramGraph | null>(null);

  protected readonly layout = computed(() => layoutGrafo(this.grafo()));
}
